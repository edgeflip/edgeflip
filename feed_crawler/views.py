import logging

from django import http
from django.conf import settings
from django.views.decorators.http import require_http_methods


LOG = logging.getLogger(__name__)


@require_http_methods(['GET', 'POST'])
def realtime_subscription(request):

    if request.method == 'GET':
        if (request.GET.get('hub.mode') == 'subscribe' and
                request.GET.get('hub.verify_token') == settings.FB_REALTIME_TOKEN):
            return http.HttpResponse(request.GET.get('hub.challenge'))
        else:
            return http.HttpResponseForbidden()
    else:
        # Do import crawly things here
        return http.HttpResponse()
