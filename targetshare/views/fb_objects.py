import logging
import urllib
import urlparse

from django import http
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404

from targetshare import models
from targetshare.tasks import db
from targetshare.views import utils

LOG = logging.getLogger(__name__)


def objects(request, fb_object_id, content_id):
    """FBObject endpoint provided to Facebook to crawl and users to click."""
    fb_object = get_object_or_404(models.relational.FBObject, fb_object_id=fb_object_id)
    client = fb_object.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)
    fb_attrs = fb_object.fbobjectattribute_set.for_datetime().get()
    choice_set_slug = request.GET.get('cssslug', '')
    campaign_id = request.GET.get('campaign_id', '')
    action_ids = request.GET.get('fb_action_ids', '').split(',')

    try:
        action_id = int(action_ids[0].strip())
    except ValueError:
        action_id = None

    # Determine user redirect URL:
    if campaign_id.isdigit():
        campaign_fbobjects = fb_object.campaignfbobjects.filter(campaign_id=campaign_id)
    else:
        campaign_fbobjects = fb_object.campaignfbobjects.all()
    source_urls = campaign_fbobjects.values_list('source_url', flat=True).distinct()

    if any(source_urls):
        # FBObject is in use by campaign(s) with dynamic-definition ("source") URL(s)
        try:
            (redirect_url,) = source_urls
        except ValueError:
            LOG.exception("Ambiguous FBObject source %r", tuple(source_urls))
            redirect_url = next(source_url for source_url in source_urls if source_url)
    else:
        # Traditionally-configured FBObject -- use ClientContent URL for redirect
        if not content.url:
            return http.HttpResponseNotFound()
        redirect_url = content.url

    if action_id:
        parsed_url = urlparse.urlparse(redirect_url)
        query_params = urlparse.parse_qsl(parsed_url.query)
        query_params.append(('fb_action_ids', action_id))
        redirect_url = parsed_url._replace(query=urllib.urlencode(query_params)).geturl()

    full_redirect_path = "{}?{}".format(
        reverse('targetshare:outgoing', args=[client.fb_app_id, redirect_url]),
        urllib.urlencode({'campaignid': campaign_id}),
    )

    # Build FBObject parameters for document:
    fb_object_url = 'https://%s%s?%s' % (
        request.get_host(),
        reverse('targetshare:objects', kwargs={
            'fb_object_id': fb_object_id,
            'content_id': content_id,
        }),
        urllib.urlencode({
            'cssslug': choice_set_slug,
            'campaign_id': campaign_id,
        }),
    )
    obj_params = {
        'page_title': fb_attrs.page_title,
        'fb_action_type': fb_attrs.og_action,
        'fb_object_type': fb_attrs.og_type,
        'fb_object_url': fb_object_url,
        'fb_app_name': client.fb_app.name,
        'fb_app_id': client.fb_app_id,
        'fb_object_title': fb_attrs.og_title,
        'fb_object_image': fb_attrs.og_image,
        'fb_object_description': fb_attrs.og_description,
        'fb_org_name': fb_attrs.org_name,
    }
    content_str = '%(fb_app_name)s:%(fb_object_type)s %(fb_object_url)s' % obj_params

    if 'facebookexternalhit' in request.META.get('HTTP_USER_AGENT', ''):
        LOG.info(
            'Facebook crawled object %s with content %s from IP %s',
            fb_object_id, content_id, utils.get_client_ip(request)
        )
    else:
        utils.set_visit(request, client.fb_app_id, start_event={
            'client_content': content,
            'campaign_id': campaign_id,
        })
        db.delayed_save.delay(
            models.relational.Event(
                visit=request.visit,
                client_content=content,
                content=content_str,
                activity_id=action_id,
                event_type='clickback',
                campaign_id=campaign_id,
            )
        )

    return render(request, 'targetshare/fb_object.html', {
        'fb_params': obj_params,
        'redirect_url': full_redirect_path,
        'content': content_str,
        'client': client,
    })
