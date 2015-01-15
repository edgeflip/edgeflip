import urllib

from django import http
from django.core.urlresolvers import reverse
from django.shortcuts import resolve_url


def urlreverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None, current_app=None,
               querymap=()):
    path = reverse(viewname, urlconf, args, kwargs, prefix, current_app)
    if not querymap:
        return path

    encoded = urllib.urlencode(querymap)
    return "{}?{}".format(path, encoded)


def urlredirect(to, *args, **kws):
    if kws.pop('permanent', False):
        redirect_class = http.HttpResponsePermanentRedirect
    else:
        redirect_class = http.HttpResponseRedirect

    querymap = kws.pop('query', ())

    path = resolve_url(to, *args, **kws)
    if querymap:
        url = "{}?{}".format(path, urllib.urlencode(querymap))
    else:
        url = path

    return redirect_class(url)
