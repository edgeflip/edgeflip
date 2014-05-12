from django import template
from django.conf import settings

from chapo import utils


register = template.Library()


def server_fallback(context, server):
    """Let the template fall back to the protocol and host of the request for
    absolute short URLs.

    """
    if server is None:
        try:
            return settings.CHAPO_SERVER
        except AttributeError:
            request = context['request']
            return '{protocol}//{host}'.format(
                protocol='https:' if request.is_secure() else 'http:',
                host=request.get_host(),
            )
    else:
        return server


@register.simple_tag(name='shorturl', takes_context=True)
def short_url(context, obj, server=None):
    """Construct the absolute, shortened URL for the given ShortenedUrl object or slug.

        {% shorturl short %}

    By default, the protocol and host of the shortened URL are copied from the request.
    To configure a default location for the routing service, either set `CHAPO_SERVER`
    in your Django settings file or pass the `server` argument; (the latter overrides
    the former).

        {% shorturl short server='https://edgefl.ip' %}

    """
    server = server_fallback(context, server)
    return utils.short_url(obj, server)


@register.simple_tag(takes_context=True)
def shorten(context, *args, **kws):
    """Return an absolute shortened URL for the given absolute long URL.

        {% shorten 'http://www.english.com/alphabet/a/b/c/defghi/' %}

    Optionally specify the shortened slug `prefix`, the `campaign` to associate
    with the mapping, and the `event_type` to associate with the mapping (defaulting
    to 'initial_redirect'). The location of the routing service, `server`, may
    also be specified; (see `short_url` and `CHAPO_SERVER`).

        {% shorten 'http://www.english.com/alphabet/a/b/c/defghi/' prefix='en' campaign=campaign server='https://edgefl.ip' %}

    """
    server = server_fallback(context, kws.pop('server', None))
    return utils.shorten(*args, server=server, **kws)
