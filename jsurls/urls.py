import re

import django.conf
from django.conf.urls import patterns, url

from jsurls import views
from jsurls.conf import settings


def jspatterns(*paths, **kws):
    prefix = kws.pop('prefix', None)
    if prefix is None:
        if settings.USE_DEBUG_URL:
            prefix = settings.DEBUG_URL
        else:
            prefix = django.conf.settings.STATIC_URL

    if not django.conf.settings.DEBUG or '://' in prefix:
        return []

    prefix_escaped = re.escape(prefix.lstrip('/'))
    patts = ('^{}{}$'.format(prefix_escaped, path) for path in paths)
    urls = (url(patt, views.serve, kwargs=kws) for patt in patts)
    return patterns('', *urls)
