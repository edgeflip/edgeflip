import logging
import urllib
import urlparse
import time

from django import http
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django.core.urlresolvers import reverse

from targetshare import forms, models
from targetshare.integration import facebook
from targetshare.tasks import db
from targetshare.tasks.integration.facebook import store_oauth_token
from targetshare.views import utils
from targetshare.tasks import ranking

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
def incoming(request, campaign_id, content_id):
    campaign = get_object_or_404(models.Campaign, pk=campaign_id)
    properties = campaign.campaignproperties.get()

    if (
        request.GET.get('error') == 'access_denied' and
        request.GET.get('error_reason') == 'user_denied'
    ):
        # OAuth denial
        # Record auth fail and redirect to error URL:
        url = "{}?{}".format(
            reverse('outgoing', args=[
                campaign.client.fb_app_id,
                urllib.quote_plus(properties.client_error_url)
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

    code = request.GET.get('code')
    if code:
        # OAuth permission
        # Enqueue task to retrieve token & fbid and record auth, and continue

        # Rebuild OAuth redirect uri from request, removing FB junk:
        redirect_query = request.GET.copy()
        for key in ('code', 'error', 'error_reason', 'error_description'):
            try:
                del redirect_query[key]
            except KeyError:
                pass

        if redirect_query:
            redirect_path = "{}?{}".format(request.path, redirect_query)
        else:
            redirect_path = request.path

        store_oauth_token.delay(
            campaign.client_id,
            code,
            request.build_absolute_uri(redirect_path),
            visit_id=request.visit.visit_id,
            campaign_id=campaign_id,
            content_id=content_id,
        )

    # Record event and redirect to the campaign faces URL
    # (with inheritance of incoming query string)
    faces_url = properties.faces_url(content_id)
    parsed_url = urlparse.urlparse(faces_url)
    query_params = '&'.join(part for part in [
        parsed_url.query,
        request.META.get('QUERY_STRING', ''),
    ] if part)
    url = parsed_url._replace(query=query_params).geturl()
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

    return utils.JsonHttpResponse({
        'database': database_up,
        'dynamo': dynamo_up,
        'facebook': facebook_up,
    })


@utils.require_visit
def faces_health_check(request):
    form = forms.FacesForm(request.GET)
    if not form.is_valid():
        return utils.JsonHttpResponse({
            'status': 'FAILURE'
        })

    data = form.cleaned_data
    campaign = data['campaign']
    content = data['content']
    fbid = data['fbid']
    token = data['token']
    num_face = data['num_face']
    client = campaign.client

    token = models.datastructs.ShortToken(
        fbid=fbid,
        appid=client.fb_app_id,
        token=token,
    )
    px3_task = ranking.proximity_rank_three(
        token=token,
        visit_id=request.visit.pk,
        campaign_id=campaign.pk,
        content_id=content.pk,
        num_faces=num_face,
    )
    px4_task = ranking.proximity_rank_four.delay(
        token=token,
        visit_id=request.visit.pk,
        campaign_id=campaign.pk,
        content_id=content.pk,
        num_faces=num_face,
        px3_task_id=px3_task.id,
    )
    start_time = time.time()
    px3_result = px4_result = None
    while time.time() - start_time < 30:
        transaction.commit_unless_managed()
        px3_result = px3_task.result
        px4_result = px4_task.result
        if px3_result and px4_result:
            break

    if all([bool(px3_result), bool(px4_result), px3_task.status == 'SUCCESS',
           px4_task.status == 'SUCCESS']):
        return utils.JsonHttpResponse({
            'status': 'SUCCESS',
        })
    else:
        return utils.JsonHttpResponse({
            'status': 'FAILURE'
        })
