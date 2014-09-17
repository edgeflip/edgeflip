from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

from jsurls.urls import jspatterns


admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('targetshare.urls')),
    url(r'^admin/', include('targetadmin.urls', namespace='targetadmin')),
    url(r'^subscriptions/', include('feed_crawler.urls', namespace='feed-crawler')),
    url(r'^reporting/', include('reporting.urls', namespace='reporting')),
    url(r'^r/', include('chapo.urls', namespace='chapo')),
)

if settings.ENV in ('development', 'staging'):
    urlpatterns += patterns('',
        url(r'^devices/', include('gimmick.urls', namespace='gimmick')),
        url(r'^mocks/', include('targetmock.urls')),
        url(r'^simpleadmin/', include(admin.site.urls)),
    )

if settings.ENV == 'development':
    urlpatterns += (
        jspatterns('js/router.js', profile='sharing') +
        jspatterns('js/router-admin.js', profile='admin') +
        jspatterns('js/router-map.js', profile='gimmick') +
        jspatterns('js/router-reports.js', profile='reporting')
    )
