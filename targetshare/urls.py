from django.conf.urls import patterns, url

urlpatterns = patterns('targetshare.views',
    url(
        r'^button/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'button', name='button'
    ),
    url(
        r'^button/(?P<campaign_slug>\S+)/$',
        'button', name='button-encoded'
    ),
    url(
        r'^frame_faces/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'frame_faces', name='frame-faces'
    ),
    url(
        r'^frame_faces/(?P<campaign_slug>\S+)/$',
        'frame_faces', name='frame-faces-encoded'
    ),
    url(r'^canvas/$', 'canvas', name='canvas'),
    url(
        r'^canvas/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'canvas_faces', name='canvas-faces'
    ),
    url(
        # Allow FB to leave off trailing slash without redirection:
        r'^canvas/(?P<campaign_slug>\S+)/?$',
        'canvas_faces', name='canvas-faces-encoded'
    ),
    url(r'^faces/$', 'faces', name='faces'),
    url(
        r'^faces-email/(?P<notification_uuid>\S+)/$',
        'faces_email_friends', name='faces-email'
    ),
    url(
        r'^canvas/faces-email/(?P<notification_uuid>\S+)/$',
        'faces_email_friends', name='canvas-faces-email'
    ),
    url(
        r'^objects/(?P<fb_object_id>\d+)/(?P<content_id>\d+)/$',
        'objects', name='objects'
    ),
    url(r'^suppress/$', 'suppress', name='suppress'),
    url(r'^record_event/$', 'record_event', name='record-event'),
    url(r'^health_check/$', 'health_check', name='health-check'),
)
