from django.shortcuts import render, get_object_or_404

from targetshare import models
from targetshare.tasks import db
from targetshare.views import utils


@utils._encoded_endpoint
@utils._require_visit
def button(request, campaign_id, content_id):
    campaign = get_object_or_404(models.relational.Campaign, campaign_id=campaign_id)
    client = campaign.client
    content = get_object_or_404(client.clientcontent, content_id=content_id)
    faces_url = campaign.campaignproperties.get().faces_url(content_id)

    # Use campaign-custom button style template name if one exists:
    try:
        # rand_assign raises ValueError if list is empty:
        button_style = campaign.campaignbuttonstyles.random_assign()
        filenames = button_style.buttonstylefiles.get()
    except (ValueError, models.relational.ButtonStyleFile.DoesNotExist):
        # The default template name will do:
        button_style = None
        html_template = 'button.html'
        css_template = 'edgeflip_client_simple.css'
    else:
        html_template = filenames.html_template or 'button.html'
        css_template = filenames.css_file or 'edgeflip_client_simple.css'

    # Record assignment:
    db.delayed_save.delay(
        models.relational.Assignment.make_managed(
            visit=request.visit,
            campaign=campaign,
            content=content,
            assignment=button_style,
            manager=campaign.campaignbuttonstyles,
        )
    )

    return render(request, utils._locate_client_template(client, html_template), {
        'goto': faces_url,
        'campaign': campaign,
        'content': content,
        'fb_params': {
            'fb_app_name': client.fb_app_name,
            'fb_app_id': client.fb_app_id
        },
        'client_css': utils._locate_client_css(client, 'edgeflip_client.css'),
        'client_css_simple': utils._locate_client_css(client, css_template),
    })
