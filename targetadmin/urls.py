from django.conf.urls import patterns, url
from django.views.generic import TemplateView

# Client URLS
urlpatterns = patterns('targetadmin.views',
    url(r'^$', 'client_views.client_list_view', name='client-list'),
    url(r'^client/(?P<client_pk>\d+)/$', 'client_views.client_detail_view', name='client-detail'),
)

urlpatterns += patterns('targetadmin.views',
    # Campaign URLs
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/summary/$', 'campaign_views.campaign_summary',
        name='campaign-summary'),
    url(r'^client/(?P<client_pk>\d+)/campaign/wizard/$', 'campaign_views.campaign_wizard',
        name='campaign-wizard'),
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/wizard/$', 'campaign_views.campaign_wizard',
        name='campaign-wizard-edit'),
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/wizard/finish/$',
        'campaign_views.campaign_wizard_finish',
        name='campaign-wizard-finish'),
    url(r'^campaign/how-it-works/$', TemplateView.as_view(template_name='targetadmin/how_it_works.html'),
        name='how-it-works'),
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/data.json$', 'campaign_views.campaign_data',
        name='campaign-data'),
    url(r'^client/(?P<client_pk>\d+)/filters.json$', 'campaign_views.available_filters',
        name='available-filters'),
)

urlpatterns += patterns('targetadmin.views',
    # Snippet URLs
    url(r'^client/(?P<client_pk>\d+)/snippets/$', 'snippets.snippets',
        name='snippets'),
    url(r'^client/(?P<client_pk>\d+)/snippets/data.json$',
        'snippets.snippet_update',
        name='snippet-update')
)

urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'logout/$', 'django.contrib.auth.views.logout', {'next_page': '/admin/'}, name='logout'),
)
