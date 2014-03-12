from django.conf.urls import patterns, include, url

from jsurls import views
from jsurls.conf import settings


def jsurl(tail, **kws):
    prefix = settings.DEBUG_URL.lstrip('/')
    pattern = '^{}{}$'.format(prefix, tail)
    return url(pattern, views.serve, kws)
