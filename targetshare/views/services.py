import json
import logging
import urllib
import urlparse

from django import http
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import db
from targetshare.views import utils

LOG = logging.getLogger(__name__)


@require_GET
@utils.require_visit
def outgoing(request, app_id, url):
    campaign_id = request.GET.get('campaignid', '')
    try:
        # '1' => True, '0' => False; default to '1':
        source = bool(int(request.GET.get('source') or '1'))
    except ValueError:
        return http.HttpResponseBadRequest('Invalid "source" flag')

    if source and campaign_id:
        try:
            campaign = get_object_or_404(models.Campaign, campaign_id=campaign_id)
        except ValueError:
            return http.HttpResponseBadRequest("Invalid campaign identifier")
        source_parameter = campaign.client.source_parameter
        if source_parameter:
            parsed_url = urlparse.urlparse(url)
            sourced_qs = (
                urlparse.parse_qsl(parsed_url.query) +
                [(source_parameter, 'ef{}'.format(campaign.pk))]
            )
            sourced_url = parsed_url._replace(
                query=urllib.urlencode(sourced_qs)
            )
            url = urlparse.urlunparse(sourced_url)

    db.delayed_save.delay(
        models.relational.Event(
            visit=request.visit,
            content=url[:1028],
            event_type='outgoing_redirect',
        )
    )
    return http.HttpResponseRedirect(url)


@utils.encoded_endpoint
@utils.require_visit
def incoming(request, campaign_id, content_id):
    campaign = get_object_or_404(models.Campaign, pk=campaign_id)
    properties = campaign.campaignproperties.get()
    url = properties.faces_url(content_id)
    db.delayed_save.delay(
        models.relational.Event(
            visit=request.visit,
            content=url[:1028],
            event_type='incoming_redirect',
        )
    )
    return http.HttpResponseRedirect(url)


def health_check(request):

    if 'elb' in request.GET:
        return http.HttpResponse("It's Alive!", status=200)

    try:
        fb_resp = facebook.client.getUrlFb("http://graph.facebook.com/6963")
    except Exception:
        facebook_up = False
    else:
        facebook_up = int(fb_resp['id']) == 6963

    try:
        database_up = models.relational.Client.objects.exists()
    except Exception:
        database_up = False

    try:
        dynamo_up = bool(models.dynamo.User.items.table.describe())
    except Exception:
        dynamo_up = False

    return http.HttpResponse(
        json.dumps({
            'database': database_up,
            'dynamo': dynamo_up,
            'facebook': facebook_up,
        }),
        content_type='application/json',
    )
