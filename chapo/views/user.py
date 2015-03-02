"""Views providing public methods to visiting users."""
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods

from core.utils import campaignstatus
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


def _handle_user_request(request, slug):
    """Helper performing all pre-response operations on behalf of a user request."""
    shortened = get_object_or_404(ShortenedUrl, slug=slug)
    campaign = shortened.campaign

    if campaign:
        set_visit(
            request,
            campaign.client.fb_app_id,
            start_event={'campaign_id': campaign.campaign_id},
            cycle=True,
        )

        if shortened.event_type:
            delayed_save.delay(
                Event(
                    visit_id=request.visit.visit_id,
                    event_type=shortened.event_type,
                    campaign_id=campaign.campaign_id,
                    content=slug,
                )
            )

        campaignstatus.handle_request(request, campaign)

    return shortened


@require_http_methods(['GET', 'HEAD'])
def main(request, slug): # routed via urls.main()
    """Return a permanent redirect (code 301) to the full URL on record for the
    given alias slug.

    """
    try:
        shortened = _handle_user_request(request, slug)
    except campaignstatus.DisallowedError as exc:
        return exc.make_error_response(friendly=True)

    content = REDIRECTION_NOTICE.format(shortened) if request.method == 'GET' else ''
    return HttpResponsePermanentRedirect(shortened.url, content)


@require_http_methods(['GET', 'POST'])
def html(request, slug):
    """Return an "OK" (code 200) response with HTML-embedded JavaScript,
    instructing JavaScript-enabled user agents to redirect the user to the full
    URL on record for the given alias slug.

    This endpoint is intended for JavaScript-enabled consumers which do not
    respect HTTP redirects. (All others, see `main`.)

    """
    try:
        shortened = _handle_user_request(request, slug)
    except campaignstatus.DisallowedError as exc:
        return exc.make_error_response(friendly=True, embedded=True)

    return render(request, 'chapo/redirect.html', {'shortened': shortened})
