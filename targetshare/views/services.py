import logging
import urllib
import urlparse
import time

from django import http
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django.core.urlresolvers import reverse

from core.utils import oauth
from core.utils.http import JsonHttpResponse

from targetshare import forms, models
from targetshare.integration import facebook
from targetshare.tasks import db
from targetshare.tasks import targeting
from targetshare.tasks.integration.facebook import store_oauth_token
from targetshare.views import OAUTH_TASK_KEY, utils

LOG = logging.getLogger(__name__)


@require_GET
@utils.require_visit
def outgoing(request, app_id, url):
    # Handle partially-qualified URLs:
    parsed_url = urlparse.urlparse(url)
    if not parsed_url.scheme:
        # URL was not fully-qualified
        request_scheme = 'https' if request.is_secure() else 'http'
        if parsed_url.netloc:
            # e.g. //www.google.com
            url = parsed_url._replace(scheme=request_scheme).geturl()
        elif url.startswith('/'):
            # e.g. /path
            url = parsed_url._replace(scheme=request_scheme, netloc=request.get_host()).geturl()
        else:
            # e.g. www.google.com
            url = "{}://{}".format(request_scheme, url)

    # Append source information:
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

    # Record event:
    db.delayed_save.delay(
        models.relational.Event(
            visit_id=request.visit.visit_id,
            campaign_id=(campaign_id or None),
            content=url[:1028],
            event_type='outgoing_redirect',
        )
    )
    return http.HttpResponseRedirect(url)


@require_GET
@utils.encoded_endpoint
@utils.require_visit
def incoming(request, api, campaign_id, content_id):
    campaign = get_object_or_404(models.Campaign, pk=campaign_id)
    properties = campaign.campaignproperties.get()

    try:
        signature = oauth.handle_incoming(request)
    except oauth.AccessDenied:
        # OAuth denial
        # Record auth fail and redirect to error URL:
        url = "{}?{}".format(
            reverse('targetshare:outgoing', args=[
                campaign.client.fb_app_id,
                properties.client_error_url
            ]),
            urllib.urlencode({'campaignid': campaign_id}),
        )
        db.bulk_create.delay([
            models.relational.Event(
                visit_id=request.visit.visit_id,
                content=url[:1028],
                event_type='incoming_redirect',
                campaign_id=campaign_id,
                client_content_id=content_id,
            ),
            models.relational.Event(
                visit_id=request.visit.visit_id,
                event_type='auth_fail',
                content='oauth',
                campaign_id=campaign_id,
                client_content_id=content_id,
            ),
        ])
        return redirect(url)

    if signature.is_valid():
        token_task = store_oauth_token.delay(
            signature.code,
            signature.redirect_uri,
            api,
            client_id=campaign.client_id,
            visit_id=request.visit.visit_id,
            campaign_id=campaign_id,
            content_id=content_id,
        )
        request.session[OAUTH_TASK_KEY] = token_task.id

    # Record event and redirect to the campaign faces URL
    # (with inheritance of incoming query string)
    url = utils.faces_url(properties.client_faces_url,
                          campaign,
                          content_id,
                          signature.redirect_query)
    db.delayed_save.delay(
        models.relational.Event(
            visit_id=request.visit.visit_id,
            content=url[:1028],
            event_type='incoming_redirect',
            campaign_id=campaign_id,
            client_content_id=content_id,
        )
    )
    return http.HttpResponseRedirect(url)


def health_check(request):

    if 'elb' in request.GET:
        return http.HttpResponse("It's Alive!", status=200)

    try:
        fb_resp = facebook.client.urlload("http://graph.facebook.com/6963")
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

    return JsonHttpResponse({
        'database': database_up,
        'dynamo': dynamo_up,
        'facebook': facebook_up,
    })


@utils.require_visit
def faces_health_check(request):
    request.visit.user_agent = 'NEW RELIC'
    request.visit.save()
    form = forms.FacesForm(request.GET)
    if not form.is_valid():
        return JsonHttpResponse(form.errors, status=400)

    data = form.cleaned_data
    campaign = data['campaign']
    content = data['content']
    fbid = data['fbid']
    token = data['token']
    api = data['api']
    num_face = data['num_face']
    client = campaign.client

    token = models.datastructs.ShortToken(
        fbid=fbid,
        appid=client.fb_app_id,
        token=token,
        api=api
    )
    px3_task = targeting.proximity_rank_three.delay(
        token=token,
        visit_id=request.visit.pk,
        campaign_id=campaign.pk,
        content_id=content.pk,
        num_faces=num_face,
    )
    px4_task = targeting.proximity_rank_four.delay(
        token=token,
        visit_id=request.visit.pk,
        campaign_id=campaign.pk,
        content_id=content.pk,
        num_faces=num_face,
        px3_task_id=px3_task.id,
    )
    ids = {'px3': px3_task.id, 'px4': px4_task.id}
    px3_result = px4_result = None
    start_time = time.time()
    while time.time() - start_time < 30:
        px3_result = px3_task.result
        px4_result = px4_task.result
        if px3_result and px4_result:
            if px3_task.status == 'SUCCESS' and px4_task.status == 'SUCCESS':
                return JsonHttpResponse({
                    'status': 'SUCCESS',
                    'id': ids,
                })
            else:
                break
        else:
            time.sleep(1)

    return JsonHttpResponse({
        'status': 'FAILURE',
        'px3_status': px3_task.status,
        'px4_status': px4_task.status,
        'id': ids,
    })
