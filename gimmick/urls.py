from django.conf.urls import patterns, url


SHARED_PATTERNS = patterns('gimmick.views',
    url(r'^engage/$', 'engage.main', name='engage'),
    url(r'^engage/(?P<task_id>[\w-]+)\.json$', 'engage.data', name='engage-data'),
    url(r'^engage/intro\.html$', 'engage.intro', name='engage-intro'),
)


urlpatterns = SHARED_PATTERNS + patterns('gimmick.views',
    url(r'^map/$', 'map.main', name='map'),
    url(r'^map/data\.json$', 'map.data', name='map-data'),
)


canvaspatterns = SHARED_PATTERNS


canvaspatterns_root = patterns('',
    # canvas home
    url(r'^$', 'gimmick.views.engage.intro', name='canvas'),
)
