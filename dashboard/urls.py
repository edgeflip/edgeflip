from django.conf.urls import patterns, url

urlpatterns = patterns('dashboard.views',
    url( r'^$', 'dashboard', name='dashboard'),
    url( r'^/chartdata/$', 'chartdata', name='chartdata'),
)
