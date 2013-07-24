import logging

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseNotFound

from edgeflip import utils, models


logger = logging.getLogger(__name__)


def _validate_client_subdomain(campaign, content, subdomain):
    ''' Verifies that the content and campaign clients are the same, and that
    the subdomain received matches what we expect on the client model
    '''

    valid = True
    if campaign.client_id != content.client_id:
        valid = False

    if campaign.client.subdomain != subdomain:
        valid = False

    return valid


def button_encoded(request, campaign_slug):

    try:
        decoded = utils.decodeDES(campaign_slug)
        campaign_id, content_id = [int(i) for i in decoded.split('/')]
    except:
        logger.exception('Failed to decrypt button')
        return HttpResponseNotFound()

    return button(request, campaign_id, content_id)


def button(request, campaign_id, content_id):
    import ipdb; ipdb.set_trace() ### XXX BREAKPOINT
    subdomain = 'fix this'
    content = get_object_or_404(models.ClientContent, content_id=content_id)
    campaign = get_object_or_404(models.Campaign, campaign_id=campaign_id)
    client = campaign.client
    if not _validate_client_subdomain(campaign, content, subdomain):
        return HttpResponseNotFound()

    faces_url = campaign.campaignproperties_set.get().faces_url
    paramsDict = {
        'fb_app_name': client.fb_app_name, 'fb_app_id': client.fb_app_id
    }
    ip = '127.0.0.1' # XXX FIXME
    session_id = request.session.id

    style_template = None
    try:
        style_recs = None
