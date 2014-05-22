from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404

from targetshare import models
from targetshare.views import utils
from targetshare.utils import encodeDES


@utils.encoded_endpoint
@utils.require_visit
def button(request, campaign_id, content_id):
    campaign = get_object_or_404(models.relational.Campaign, campaign_id=campaign_id)
    client = campaign.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)
    faces_url = '{}{}{}'.format(
        'https://' if request.is_secure() else 'http://',
        request.get_host(),
        reverse('incoming-encoded', args=[encodeDES('%s/%s' % (campaign_id, content_id))])
    )

    page_styles = utils.assign_page_styles(
        request.visit,
        models.relational.Page.BUTTON,
        campaign,
        content,
    )

    return render(request, 'targetshare/button.html', {
        'goto': faces_url,
        'campaign': campaign,
        'content': content,
        'campaign_css': page_styles,
        'fb_params': {
            'fb_app_name': client.fb_app_name,
            'fb_app_id': client.fb_app_id
        },
    })
