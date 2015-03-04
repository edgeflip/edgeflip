from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView

from core.utils.encryptedslug import API_DEFAULT


# App-review hackery:
class CanvasRedirect(TemplateView):

    template_name = 'chapo/redirect.html'
    url = None

    def get_context_data(self, **kwargs):
        context = super(CanvasRedirect, self).get_context_data(**kwargs)
        context['url'] = self.url
        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

canvas_redirect = csrf_exempt(
    CanvasRedirect.as_view(url='https://app.edgeflip.com/r/22demo-XAiTghmz/')
)


urlpatterns = patterns('targetshare.views',
    # button
    url(
        r'^button/(?P<api>[.\d]+)/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'button.button', name='button'
    ),
    url(
        r'^button/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'button.button', {'api': API_DEFAULT}, name='button-default'
    ),
    url(
        r'^button/(?P<encrypted_slug>[^/\s]+)/$',
        'button.button', name='button-encoded'
    ),

    # frame-faces
    url(
        r'^frame_faces/(?P<api>[.\d]+)/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'faces.frame_faces', name='frame-faces'
    ),
    url(
        r'^frame_faces/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'faces.frame_faces', {'api': API_DEFAULT}, name='frame-faces-default'
    ),
    url(
        r'^frame_faces/(?P<encrypted_slug>[^/\s]+)/$',
        'faces.frame_faces', name='frame-faces-encoded'
    ),

    # canvas (frame-faces)
    url(
        r'^canvas/(?P<api>[.\d]+)/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'faces.frame_faces', {'canvas': True}, name='canvas-faces'
    ),
    url(
        r'^canvas/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'faces.frame_faces', {'api': API_DEFAULT, 'canvas': True}, name='canvas-faces-default'
    ),
    url(
        # Allow FB to leave off trailing slash without redirection
        r'^canvas/(?P<encrypted_slug>[^/\s]+)/?$',
        'faces.frame_faces', {'canvas': True}, name='canvas-faces-encoded'
    ),

    # canvas home
    url(r'^canvas/$',
        canvas_redirect,
        # 'faces.canvas',
        name='canvas'),

    # faces
    url(r'^faces/$', 'faces.faces', name='faces'),

    # faces-email
    url(
        r'^faces-email/(?P<notification_uuid>[^/\s]+)/$',
        'faces.faces_email_friends', name='faces-email'
    ),
    url(
        r'^canvas/faces-email/(?P<notification_uuid>[^/\s]+)/$',
        'faces.faces_email_friends', name='canvas-faces-email'
    ),

    # fb-objects
    url(
        r'^objects/(?P<fb_object_id>\d+)/(?P<content_id>\d+)/$',
        'fb_objects.objects', name='objects'
    ),

    # incoming
    url(r'^incoming/(?P<api>[.\d]+)/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'services.incoming', name='incoming'),
    url(r'^incoming/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'services.incoming', {'api': API_DEFAULT}, name='incoming-default'),
    url(r'^incoming/(?P<encrypted_slug>[^/\s]+)/$',
        'services.incoming', name='incoming-encoded'),

    url(r'^outgoing/(?P<app_id>\d+)/(?P<url>.+)/$', 'services.outgoing',
        name='outgoing'),
    url(r'^suppress/$', 'events.suppress', name='suppress'),
    url(r'^record_event/$', 'events.record_event', name='record-event'),

    url(r'^health_check/$', 'services.health_check', name='health-check'),
    url(r'^health_check/faces/$', 'services.faces_health_check',
        name='faces-health-check'),
)
