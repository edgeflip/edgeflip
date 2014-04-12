import json
import logging

from django import http
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

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
            LOG.exception('Invalid user update entry')
        except ValueError:
            LOG.exception('Invalid user update FBID: %s', entry['uid'])
        else:
            tasks.crawl_user.delay(fbid)

    return http.HttpResponse()
