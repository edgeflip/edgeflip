from django.conf.urls import patterns, url

urlpatterns = patterns('reporting.views',
    url(r'^$', 'main.main', name='main'),  # main client template
    url(r'client/(?P<client_pk>\d+)/summary/$', 'client_summary.client_summary', name='client_summary'), # client summary data for all campaigns
    url(r'client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/hourly/$', 'campaign_hourly.campaign_hourly', name='campaign_hourly'),  # hourly data for a particular campaign
)

urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'logout/$', 'django.contrib.auth.views.logout', {'next_page': '/reporting/'}, name='logout'),
)
