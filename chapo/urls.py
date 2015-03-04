from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.http import HttpResponsePermanentRedirect
from django.views.decorators.csrf import csrf_exempt

from chapo.views import user, api


@csrf_exempt # see: `views.api.require_api_key.csrf_exempt`
def main(request, slug):
    """Route PUT requests for slug to the API, and other methods to the user
    redirector.

    """
    handler = api.upsert_slug if request.method == 'PUT' else user.main
    return handler(request, slug)


@csrf_exempt # see: `views.api.require_api_key.csrf_exempt`
def main_slashless(request, slug):
    """Route PUT requests for slug to the API, and issue a permanent redirect
    to the user redirector's canonical endpoint to others.

    """
    if request.method == 'PUT':
        return api.upsert_slug(request, slug)
    else:
        canon_path = reverse('chapo:main', args=[slug],
                             current_app=request.resolver_match.namespace)
        return HttpResponsePermanentRedirect(canon_path)


urlpatterns = patterns('',
    # Handle users *and* API PUT
    url(r'^(?P<slug>[-\w]+)/$', main, name='main'), # ends in slash
    url(r'^(?P<slug>[-\w]+)$', main_slashless, name='main-slashless'), # ends without slash
)

urlpatterns += patterns('chapo.views.user',
    url(r'^(?P<slug>[-\w]+)\.html$', 'html', name='html'),
)

urlpatterns += patterns('chapo.views.api',
    url(r'^(?P<slug>[-\w]+)\.(?P<extension>\w+)$', 'dump_slug', name='dump-slug'),
    url(r'^$', 'shorten_url', name='shorten-url'),
)
