from django.conf.urls import patterns, url
from django.views.generic import TemplateView

# Client URLS
urlpatterns = patterns('targetadmin.views.client_views',
    url(r'^$', 'client_list_view', name='client-list'),
    url(r'^client/(?P<client_pk>\d+)/$', 'client_detail_view', name='client-detail'),
)

# Campaign URLs
urlpatterns += patterns('targetadmin.views.campaign_views',
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/summary/$',
        'campaign_summary',
        name='campaign-summary'),
    url(r'^client/(?P<client_pk>\d+)/campaign/wizard/$',
        'campaign_wizard',
        name='campaign-wizard'),
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/wizard/$',
        'campaign_wizard',
        name='campaign-wizard-edit'),
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/wizard/finish/$',
        'campaign_summary',
        {'wizard': True},
        'campaign-wizard-finish'),
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/data.json$',
        'campaign_data',
        name='campaign-data'),
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<campaign_pk>\d+)/publish$',
        'publish_campaign',
        name='publish-campaign'),
    url(r'^client/(?P<client_pk>\d+)/filters.json$',
        'available_filters',
        name='available-filters'),
    url(r'^campaign/how-it-works/$',
        TemplateView.as_view(template_name='targetadmin/how_it_works.html'),
        name='how-it-works'),
)

# Snippet URLs
urlpatterns += patterns('targetadmin.views.snippets',
    url(r'^client/(?P<client_pk>\d+)/snippets/$',
        'snippets',
        name='snippets'),
    url(r'^client/(?P<client_pk>\d+)/snippets/data.json$',
        'snippet_update',
        name='snippet-update'),
)

urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'logout/$', 'django.contrib.auth.views.logout', {'next_page': '/admin/'}, name='logout'),
)
