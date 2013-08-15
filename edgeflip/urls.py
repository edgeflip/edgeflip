from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('targetshare.urls')),
    url(r'^mocks/', include('targetmock.urls')),
    url(r'^admin/', include('targetadmin.urls')),
    url(r'^dashboard/', include('dashboard.urls')),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('', url(r'^simpleadmin/', include(admin.site.urls)))
