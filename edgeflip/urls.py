from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('targetshare.urls')),
    url(r'^admin/', include('targetadmin.urls')),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('',
        url(r'^mocks/', include('targetmock.urls')),
        url(r'^simpleadmin/', include(admin.site.urls))
    )
