from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView

from core.utils.encryptedslug import API_DEFAULT


# App-review hackery #
class CanvasRedirect(TemplateView):

    template_name = 'chapo/redirect.html'
    url = None

    def get_context_data(self, **kwargs):
        context = super(CanvasRedirect, self).get_context_data(**kwargs)
        context['url'] = self.url
        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

CANVAS_REDIRECT = csrf_exempt(
    CanvasRedirect.as_view(url='https://app.edgeflip.com/r/22demo-XAiTghmz/')
)


# Internally-shared patterns #

# Patterns copied everywhere (just frame-faces)
# (These aren't always namespaced the same, so they're not simply SHARED_PATTERNS.)
FRAME_FACES = patterns('targetshare.views',
    # frame-faces
    url(
        r'^(?P<api>[.\d]+)/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'faces.frame_faces', name='frame-faces'
    ),
    url(
        r'^(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'faces.frame_faces', {'api': API_DEFAULT}, 'frame-faces-default'
    ),
    url(
        # Allow FB to leave off trailing slash without redirection
        r'^(?P<encrypted_slug>[^/\s]{2,})/?$',
        'faces.frame_faces', name='frame-faces-encoded'
    ),
)

# Patterns shared between the main app endpoint and the canvas namespace
SHARED_PATTERNS = patterns('targetshare.views',
    # faces-email
    url(
        r'^faces-email/(?P<notification_uuid>[^/\s]+)/$',
        'faces.faces_email_friends', name='faces-email'
    ),
)

# Patterns shared between the main app endpoint and the legacy endpoint
# (Once legacypatterns is removed, these can be merged entirely with urlpatterns.)
LEGACY_PATTERNS = patterns('targetshare.views',
    # fb-objects
    url(
        r'^objects/(?P<fb_object_id>\d+)/(?P<content_id>\d+)/$',
        'fb_objects.objects', name='objects'
    ),

    # incoming
    url(
        r'^incoming/(?P<api>[.\d]+)/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'services.incoming', name='incoming'
    ),
    url(
        r'^incoming/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'services.incoming', {'api': API_DEFAULT}, 'incoming-default'
    ),
    url(
        r'^incoming/(?P<encrypted_slug>[^/\s]{2,})/$',
        'services.incoming', name='incoming-encoded'
    ),
)


# URL pattern exports #

# Basic patterns (the module's default export)
urlpatterns = SHARED_PATTERNS + LEGACY_PATTERNS + patterns('targetshare.views',
    # button
    url(
        r'^button/(?P<api>[.\d]+)/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'button.button', name='button'
    ),
    url(
        r'^button/(?P<campaign_id>\d+)/(?P<content_id>\d+)/$',
        'button.button', {'api': API_DEFAULT}, 'button-default'
    ),
    url(
        r'^button/(?P<encrypted_slug>[^/\s]{2,})/$',
        'button.button', name='button-encoded'
    ),

    # faces
    url(r'^faces/$', 'faces.faces', name='faces'),

    # frame-faces
    url(r'^frame/', include(FRAME_FACES)),

    # services
    url(r'^outgoing/(?P<app_id>\d+)/(?P<url>.+)/$', 'services.outgoing', name='outgoing'),
    url(r'^suppress/$', 'events.suppress', name='suppress'),
    url(r'^record/$', 'events.record_event', name='record-event'),

    url(r'^health/$', 'services.health_check', name='health-check'),
    url(r'^health/faces/$', 'services.faces_health_check', name='faces-health-check'),
)


# Patterns intended for installation under a canvas namespace
canvaspatterns = SHARED_PATTERNS + FRAME_FACES


# Patterns that *must* install at the canvas *root* (e.g. the canvas home page)
canvaspatterns_root = patterns('targetshare.views',
    # canvas home
    # url(r'^$',
    #     CANVAS_REDIRECT,
    #     # 'faces.canvas',
    #     name='canvas'),

    # LEGACY canvas frame-faces
    # TODO: REMOVE. These could conflict with other apps.
    # There should only be one route at the canvas root.
    url(r'^', include(FRAME_FACES)),
)


# TODO: REMOVE once we're sure no-one will be looking for these routes any longer
legacypatterns = LEGACY_PATTERNS
