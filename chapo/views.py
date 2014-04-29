from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

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
    content = REDIRECTION_NOTICE.format(shortened) if request.method == 'GET' else ''
    return HttpResponsePermanentRedirect(shortened.url, content)
