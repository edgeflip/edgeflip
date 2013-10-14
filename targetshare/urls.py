from django.conf.urls import patterns, url

urlpatterns = patterns('targetshare.views',
    url(
        r'^button/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'button.button', name='button'
    ),
    url(
        r'^button/(?P<campaign_slug>\S+)/$',
        'button.button', name='button-encoded'
    ),
    url(
        r'^frame_faces/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'faces.frame_faces', name='frame-faces'
    ),
    url(
        r'^frame_faces/(?P<campaign_slug>\S+)/$',
        'faces.frame_faces', name='frame-faces-encoded'
    ),
    url(r'^canvas/$', 'faces.canvas', name='canvas'),
    url(
        r'^canvas/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'faces.canvas_faces', name='canvas-faces'
    ),
    url(
        # Allow FB to leave off trailing slash without redirection:
        r'^canvas/(?P<campaign_slug>\S+)/?$',
        'faces.canvas_faces', name='canvas-faces-encoded'
    ),
    url(r'^faces/$', 'faces.faces', name='faces'),
    url(
        r'^faces-email/(?P<notification_uuid>\S+)/$',
        'faces.faces_email_friends', name='faces-email'
    ),
    url(
        r'^canvas/faces-email/(?P<notification_uuid>\S+)/$',
        'faces.faces_email_friends', name='canvas-faces-email'
    ),
    url(
        r'^objects/(?P<fb_object_id>\d+)/(?P<content_id>\d+)/$',
        'fb_objects.objects', name='objects'
    ),
    url(r'^suppress/$', 'events.suppress', name='suppress'),
    url(r'^outgoing/(?P<app_id>\d+)/(?P<url>.+)/$', 'services.outgoing',
        name='outgoing'),
    url(r'^record_event/$', 'events.record_event', name='record-event'),
    url(r'^health_check/$', 'services.health_check', name='health-check'),
)
