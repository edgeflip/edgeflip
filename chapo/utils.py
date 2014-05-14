import itertools
import logging
import uuid

import django.core.cache
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.utils.text import slugify

from chapo.models import ShortenedUrl


LOG = logging.getLogger('crow')


def short_url(obj, server=None):
    """Construct the shortened URL for the given ShortenedUrl object or slug.

    By default, the shortened URL consists only of the full path, according to
    the installation of chapo's urls. To configure a default location for the routing
    service, and have this helper return absolute URLs, either set `CHAPO_SERVER`
    in your Django settings file or pass the `server` argument; (the latter overrides
    the former).

        >> short_url(obj)
        '/r/jSgnUTqptPrV/'

        >> short_url(obj, 'https://edgefl.ip')
        'https://edgefl.ip/r/jSgnUTqptPrV/'

    """
    if server is None:
        server = getattr(settings, 'CHAPO_SERVER', '')

    slug = getattr(obj, 'slug', obj)
    path = reverse('chapo:main', args=(slug,))

    return '{server}{path}'.format(server=server, path=path)


def shorten(long_url, prefix='', campaign=None, event_type='initial_redirect',
            max_attempts=100, cache_timeout=None, server=None):
    """Return a shortened URL for the given absolute long URL.

        >>> shorten('http://www.english.com/alphabet/a/b/c/defghi/')
        '/r/jSgnUTqptPrV/'

    Optionally specify the shortened slug `prefix`, a `campaign` to associate
    with the mapping, and the `event_type` to associate with the mapping (defaulting
    to 'initial_redirect'). The location of the routing service, `server`, may
    also be specified; (see `short_url` and `CHAPO_SERVER`).

        >>> shorten(
        ...     'http://www.english.com/alphabet/a/b/c/defghi/',
        ...     prefix='en',
        ...     campaign=1,
        ...     event_type='custom_redirect',
        ...     server='https://edgefl.ip',
        ... )
        'https://edgefl.ip/r/en-jSgnUTqpt/'

    In the case of collision, multiple attempts are made to generate a novel slug,
    (defaulting to 100), which may be configured via `max_attempts`; (pass 0 to try
    indefinitely).

    This helper uses any cache configured as the default, to avoid unnecessary
    database inserts and redundant mappings. The default cache expiration is 0
    seconds (never). This default may be changed by setting `CHAPO_CACHE_TIMEOUT`
    in your Django settings file, or by passing the `cache_timeout` argument;
    (the latter overrides the former).

    """
    campaign_id = getattr(campaign, 'pk', campaign)
    cache_key = 'shorturl|{event_type}|{prefix}|{campaign_id}|{url}'.format(
        event_type=event_type,
        prefix=str(slugify(unicode(prefix))) if prefix else '',
        campaign_id=campaign_id or '',
        url=uuid.uuid5(uuid.NAMESPACE_URL, long_url.encode('utf-8')).hex,
    )
    slug = django.core.cache.cache.get(cache_key)

    if slug is None:
        for count in itertools.count(1):
            slug = ShortenedUrl.make_slug(prefix)
            try:
                ShortenedUrl.objects.create(
                    slug=slug,
                    campaign_id=campaign_id or None,
                    event_type=event_type,
                    url=long_url,
                )
            except IntegrityError:
                # slug was not unique, try again?
                if count == max_attempts:
                    raise
            else:
                if count > 1:
                    LOG.warning("shorten required %s attempts", count)
                break # done!

        if cache_timeout is None:
            cache_timeout = getattr(settings, 'CHAPO_CACHE_TIMEOUT', 0)
        django.core.cache.cache.set(cache_key, slug, cache_timeout)

    return short_url(slug, server)
