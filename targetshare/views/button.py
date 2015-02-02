from django.shortcuts import render, get_object_or_404

from core.utils import sharingurls
from targetshare import models
from targetshare.views import utils


@utils.encoded_endpoint
@utils.require_visit
def button(request, api, campaign_id, content_id):
    campaign = get_object_or_404(models.relational.Campaign, campaign_id=campaign_id)
    client = campaign.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)

    goto = sharingurls.incoming_redirect(request.is_secure(), request.get_host(), campaign, content)

    page_styles = utils.assign_page_styles(
        request.visit,
        models.relational.Page.BUTTON,
        campaign,
        content,
    )

    return render(request, 'targetshare/button.html', {
        'goto': goto,
        'campaign': campaign,
        'content': content,
        'campaign_css': page_styles,
        'fb_params': {
            'fb_app_name': client.fb_app.name,
            'fb_app_id': client.fb_app_id
        },
    })
