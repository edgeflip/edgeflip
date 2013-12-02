import json
import logging

from django import http
from django.conf import settings
from django.views.decorators.http import require_http_methods

from targetshare.models import dynamo
from targetshare.tasks import ranking


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
        # Do important crawly things here
        data = json.loads(request.POST['data'])
        for entry in data['entry']:
            try:
                token = dynamo.Token.items.query(fbid__eq=entry['uid'])[0]
            except IndexError:
                # Somehow no tokens for this user
                LOG.exception('No tokens found for {}'.format(
                    entry['uid']))
            else:
                # Run px4 on the user, but place it on a different queue
                # as to not disturb the main user flow
                ranking.proximity_rank_four.apply_async(
                    args=[False, token.fbid, token],
                    routing_key='bg.px4'
                )
        return http.HttpResponse()
