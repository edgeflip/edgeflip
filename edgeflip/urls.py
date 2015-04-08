from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

from jsurls.urls import jspatterns

import gimmick.urls
import targetshare.urls


admin.autodiscover()

urlpatterns = patterns('',
    # chapo
    url(r'^r/', include('chapo.urls', namespace='chapo', app_name='chapo')),
    url(r'^canvas/r/', include('chapo.urls', namespace='chapo-embedded', app_name='chapo')),

    # targetshare
    url(r'^share/', include(targetshare.urls.urlpatterns,
                            namespace='targetshare', app_name='targetshare')),
    url(r'^canvas/share/', include(targetshare.urls.canvaspatterns,
                                   namespace='targetshare-canvas', app_name='targetshare')),
    url(r'^canvas/', include(targetshare.urls.canvaspatterns_root,
                             namespace='targetshare-canvas-root', app_name='targetshare')),
    url(r'^', include(targetshare.urls.legacypatterns)),

    # gimmick
    url(r'^devices/', include(gimmick.urls.urlpatterns,
                              namespace='gimmick', app_name='gimmick')),
    url(r'^canvas/devices/', include(gimmick.urls.canvaspatterns,
                                     namespace='gimmick-canvas', app_name='gimmick')),
    url(r'^canvas/', include(gimmick.urls.canvaspatterns_root,
                             namespace='gimmick-canvas-root', app_name='gimmick')),

    # etc.
    url(r'^admin/', include('targetadmin.urls', namespace='targetadmin')),
    url(r'^subscriptions/', include('feed_crawler.urls', namespace='feed-crawler')),
    url(r'^reporting/', include('reporting.urls', namespace='reporting')),
)

if settings.ENV in ('development', 'staging'):
    urlpatterns += patterns('',
        url(r'^devices/', include(gimmick.urls.demopatterns,
                                  namespace='gimmick', app_name='gimmick')),
        url(r'^mocks/', include('targetmock.urls')),
        url(r'^simpleadmin/', include(admin.site.urls)),
    )

if settings.ENV == 'development':
    urlpatterns += (
        jspatterns('js/router-sharing.js', profile='sharing') +
        jspatterns('js/router-admin.js', profile='admin') +
        jspatterns('js/router-devices.js', profile='gimmick') +
        jspatterns('js/router-reports.js', profile='reporting')
    )
