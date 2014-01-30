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
        if (request.GET.get('hub.mode') == 'subscribe' and
                request.GET.get('hub.verify_token') == settings.FB_REALTIME_TOKEN):
            return http.HttpResponse(request.GET.get('hub.challenge'))
        else:
            return http.HttpResponseForbidden()
    else:
        data = json.loads(request.body)
        for entry in data['entry']:
            try:
                token = dynamo.Token.items.query(fbid__eq=int(entry['uid']))[0]
            except IndexError:
                # Somehow no tokens for this user
                LOG.exception('No tokens found for {}'.format(
                    entry['uid']))
            except ValueError:
                LOG.exception('Invalid FBID {}'.format(entry['uid']))
            else:
                # Run px4 on the user, but place it on a different queue
                # as to not disturb the main user flow
                tasks.crawl_user.delay(token)
        return http.HttpResponse()
