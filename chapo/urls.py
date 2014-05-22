from django.conf.urls import patterns, url


urlpatterns = patterns('chapo.views',
    url(r'^(?P<slug>[-\w]+)/$', 'main', name='main'),
)
