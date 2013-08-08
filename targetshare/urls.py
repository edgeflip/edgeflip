from django.conf.urls import patterns, url

urlpatterns = patterns('targetshare.views',
    url(
        r'^button/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'button', name='button'
    ),
    url(
        r'^button/(?P<campaign_slug>\S+)/$',
        'button_encoded', name='button-encoded'
    ),
    url(
        r'^frame_faces/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'frame_faces', name='frame-faces'
    ),
    url(
        r'^frame_faces/(?P<campaign_slug>\S+)/$',
        'frame_faces_encoded', name='frame-faces-encoded'
    ),
    url(r'^faces/$', 'faces', name='faces'),
    url(
        r'^objects/(?P<fb_object_id>\d+)/(?P<content_id>\d+)/$',
        'objects', name='objects'
    ),
    url(r'^suppress/$', 'suppress', name='suppress'),
    url(r'^record_event/$', 'record_event', name='record-event'),
    url(r'^canvas/$', 'canvas', name='canvas'),
    url(r'^health_check/$', 'health_check', name='health-check'),
)
