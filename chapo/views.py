import logging

from django import http
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from targetshare.models.relational import Event
from targetshare.tasks.db import delayed_save
from targetshare.views.utils import set_visit

from chapo.models import ShortenedUrl


LOG = logging.getLogger('crow')

FORBIDDEN_NOTICE = """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Page under construction</h1>
        <p>Perhaps you'd like to log in first?</p>
        <p>Otherwise, check back in a bit!</p>
    </body>
    </html>
"""

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

        campaign_status = campaign.campaignproperties.only('status').get()
        if campaign_status.status == campaign_status.Status.DRAFT:
            # Campaign is as yet unpublished

            if not request.user.is_superuser and not request.user.groups.filter(client=campaign.client).exists():
                # User is unauthenticated or unauthorized; boot 'em:
                LOG.warning("Received unauthorized request for draft campaign (%s)",
                            campaign.campaign_id, extra={'request': request})
                delayed_save.delay(
                    Event(
                        visit_id=request.visit.visit_id,
                        event_type='preview_denied', # TODO: do a first-or-create later
                        campaign_id=campaign.campaign_id,
                        content=request.user.username,
                    )
                )
                content = FORBIDDEN_NOTICE if request.method == 'GET' else ''
                return http.HttpResponseForbidden(content)

            # User is an authenticated member of the campaign client's auth group;
            # just note that we'll be giving them a preview:
            delayed_save.delay(
                Event(
                    visit_id=request.visit.visit_id,
                    event_type='client_preview', # TODO: do a first-or-create later
                    campaign_id=campaign.campaign_id,
                    content=request.user.username,
                )
            )

    content = REDIRECTION_NOTICE.format(shortened) if request.method == 'GET' else ''
    return http.HttpResponsePermanentRedirect(shortened.url, content)
