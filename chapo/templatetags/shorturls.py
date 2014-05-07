import itertools
import logging
import uuid

import django.core.cache
from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.utils.text import slugify

from chapo.models import ShortenedUrl


LOG = logging.getLogger('crow')

SHORTEN_EVENT_TYPE = 'initial_redirect'
SHORTEN_MAX_ATTEMPTS = 100 # set to 0 to try infinitely

register = template.Library()


@register.simple_tag(name='shorturl', takes_context=True)
def short_url(context, obj, protocol=''):
    """Construct the absolute, shortened URL from the given ShortenedUrl object or slug.

        {% shorturl short %}

    Optionally specify the protocol:

        {% shorturl short protocol='https:' %}

    """
    try:
        host = settings.CHAPO_REDIRECTOR_DOMAIN
    except AttributeError:
        request = context['request']
        host = request.get_host()

    slug = getattr(obj, 'slug', obj)
    path = reverse('chapo:main', args=(slug,))

    return '{protocol}//{host}{path}'.format(protocol=protocol, host=host, path=path)


@register.simple_tag(takes_context=True)
def shorten(context, long_url, prefix='', campaign=None, protocol=''):
    """Return an absolute, shortened URL for the given absolute, long URL.

        {% shorten 'http://www.english.com/alphabet/a/b/c/defghi/' %}

    Optionally specify the shortened slug prefix, a campaign to associate with
    the mapping, and an HTTP protocol for the shortened URL:

        {% shorten 'http://www.english.com/alphabet/a/b/c/defghi/' prefix='en' campaign=campaign protocol='https:' %}

    """
    cache_key = 'shorturl|{event_type}|{prefix}|{campaign_id}|{url}'.format(
        event_type=SHORTEN_EVENT_TYPE,
        prefix=str(slugify(unicode(prefix))) if prefix else '',
        campaign_id=getattr(campaign, 'pk', campaign) or '',
        url=uuid.uuid5(uuid.NAMESPACE_URL, long_url.encode('utf-8')).hex,
    )
    slug = django.core.cache.cache.get(cache_key)

    if slug is None:
        for count in itertools.count(1):
            slug = ShortenedUrl.make_slug(prefix)
            try:
                ShortenedUrl.objects.create(
                    slug=slug,
                    campaign=campaign,
                    event_type=SHORTEN_EVENT_TYPE,
                    url=long_url,
                )
            except IntegrityError:
                # slug was not unique, try again?
                if count == SHORTEN_MAX_ATTEMPTS:
                    raise
            else:
                if count > 1:
                    LOG.warning("shorten required %s attempts", count)
                break # done!

        timeout = getattr(settings, 'CHAPO_CACHE_TIMEOUT', 0)
        django.core.cache.cache.set(cache_key, slug, timeout)

    return short_url(context, slug, protocol)
