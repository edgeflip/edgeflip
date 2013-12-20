from django.conf.urls import patterns, url

urlpatterns = patterns('feed_crawler.views',
    url(r'^realtime-feed/$', 'realtime_subscription', name='realtime-subscription'),
)
