from django.conf.urls import patterns, url

urlpatterns = patterns('gimmick.views',
    url(r'^map/$', 'map.main', name='map'),
    url(r'^map/data.json$', 'map.data', name='map-data'),
)
