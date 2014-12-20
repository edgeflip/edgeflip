from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from core.utils.campaignstatus import CampaignStatusHandler
from targetshare.models.relational import Event
from targetshare.tasks.db import delayed_save
from targetshare.views.utils import set_visit

from chapo.models import ShortenedUrl


REDIRECTION_NOTICE = """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Redirection Service</h1>
        <p>The requested resource ({0.slug}) is a shortened alias.</p>
        <p>Please refer to <a href="{0.url}">{0.url}</a>.</p>
    </body>
    </html>
"""


@require_http_methods(['GET', 'HEAD'])
def main(request, slug):
    """Return a permanent redirect (code 301) to the full URL on record for the
    given alias slug.

    """
    shortened = get_object_or_404(ShortenedUrl, slug=slug)
    campaign = shortened.campaign

    if campaign and shortened.event_type:
        app_id = campaign.client.fb_app_id
        set_visit(
            request,
            app_id,
            start_event={'campaign_id': campaign.campaign_id},
            cycle=True,
        )
        delayed_save.delay(
            Event(
                visit_id=request.visit.visit_id,
                event_type=shortened.event_type,
                campaign_id=campaign.campaign_id,
                content=slug,
            )
        )

        campaign_status = CampaignStatusHandler.handle_request(request, campaign)
        if not campaign_status.is_allowed:
            return campaign_status.make_response(friendly=True)

    content = REDIRECTION_NOTICE.format(shortened) if request.method == 'GET' else ''
    return HttpResponsePermanentRedirect(shortened.url, content)
