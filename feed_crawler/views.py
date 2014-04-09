import json
import logging

from django import http
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from targetshare.models import dynamo
from feed_crawler import tasks


LOG = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def realtime_subscription(request):
    if request.method == 'GET':
        if (
            request.GET.get('hub.mode') == 'subscribe' and
            request.GET.get('hub.verify_token') == settings.FB_REALTIME_TOKEN
        ):
            return http.HttpResponse(request.GET.get('hub.challenge'))

        return http.HttpResponseForbidden()

    data = json.load(request)
    for entry in data['entry']:
        try:
            fbid = int(entry['uid'])
        except KeyError:
            LOG.exception('Invalid user update entry %s', entry)
        except ValueError:
            LOG.exception('Invalid FBID %s', entry['uid'])
        else:
            tokens = dynamo.Token.items.query(fbid__eq=fbid)
            if tokens:
                # Grab the most recent token:
                token = sorted(tokens, key=lambda token: token.expires)[-1]
                # Run px4 on the user, but via a different queue, so as to
                # not disturb the main user flow:
                tasks.crawl_user.delay(token.fbid, token.appid)
            else:
                # Somehow no tokens for this user
                LOG.error('No tokens found for %s', fbid)

    return http.HttpResponse()
