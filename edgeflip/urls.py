from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from jsurls.urls import jsurl


admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('targetshare.urls')),
    url(r'^admin/', include('targetadmin.urls', namespace='targetadmin')),
    url(r'^subscriptions/', include('feed_crawler.urls', namespace='feed-crawler')),
    url(r'^reporting/', include('reporting.urls', namespace='reporting')),
)

if settings.ENV in ('development', 'staging'):
    urlpatterns += patterns('',
        url(r'^devices/', include('gimmick.urls', namespace='gimmick')),
        url(r'^mocks/', include('targetmock.urls')),
        url(r'^simpleadmin/', include(admin.site.urls)),
    )

if settings.ENV == 'development':
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('', jsurl('js/router.js'))
