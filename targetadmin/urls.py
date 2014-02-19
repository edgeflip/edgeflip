from django.conf.urls import patterns, url


# Client URLS
urlpatterns = patterns('targetadmin.views',
    url(r'^$', 'client_views.client_list_view', name='client-list'),
    url(r'^client/(?P<client_pk>\d+)/$', 'client_views.client_detail_view', name='client-detail'),
    url(r'^client/new/$', 'client_views.client_form_view', name='client-new'),
    url(r'^client/(?P<client_pk>\d+)/edit/$', 'client_views.client_form_view', name='client-edit'),
)

urlpatterns += patterns('targetadmin.views',
    # Content URLs
    url(r'^client/(?P<client_pk>\d+)/content/$', 'content_views.content_list',
        name='content-list'),
    url(r'^client/(?P<client_pk>\d+)/content/(?P<pk>\d+)/$', 'content_views.content_detail',
        name='content-detail'),
    url(r'^client/(?P<client_pk>\d+)/content/new/$', 'content_views.content_edit',
        name='content-new'),
    url(r'^client/(?P<client_pk>\d+)/content/edit/(?P<pk>\d+)/$', 'content_views.content_edit',
        name='content-edit'),
)

urlpatterns += patterns('targetadmin.views',
    # FB Object URLs
    url(r'^client/(?P<client_pk>\d+)/fbobject/$', 'fbobject_views.fb_object_list',
        name='fb-obj-list'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/(?P<pk>\d+)/$', 'fbobject_views.fb_object_detail',
        name='fb-obj-detail'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/new/$', 'fbobject_views.fb_object_edit',
        name='fb-obj-new'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/edit/(?P<pk>\d+)/$', 'fbobject_views.fb_object_edit',
        name='fb-obj-edit'),
)

urlpatterns += patterns('targetadmin.views',
    # Filter URLs
    url(r'^client/(?P<client_pk>\d+)/filter/$', 'filter_views.filter_list',
        name='filter-list'),
    url(r'^client/(?P<client_pk>\d+)/filter/(?P<pk>\d+)/$', 'filter_views.filter_detail',
        name='filter-detail'),
    url(r'^client/(?P<client_pk>\d+)/filter/new/$', 'filter_views.filter_new',
        name='filter-new'),
    url(r'^client/(?P<client_pk>\d+)/filter/add/$', 'filter_views.add_filter',
        name='filter-add'),
    url(r'^client/(?P<client_pk>\d+)/filter/edit/(?P<pk>\d+)/$', 'filter_views.filter_edit',
        name='filter-edit'),
)

urlpatterns += patterns('targetadmin.views',
    # Choice Set URLs
    url(r'^client/(?P<client_pk>\d+)/cs/$', 'choice_set_views.cs_list',
        name='cs-list'),
    url(r'^client/(?P<client_pk>\d+)/cs/(?P<pk>\d+)/$', 'choice_set_views.cs_detail',
        name='cs-detail'),
    url(r'^client/(?P<client_pk>\d+)/cs/new/$', 'choice_set_views.cs_new',
        name='cs-new'),
    url(r'^client/(?P<client_pk>\d+)/cs/edit/(?P<pk>\d+)/$', 'choice_set_views.cs_edit',
        name='cs-edit'),
)

urlpatterns += patterns('targetadmin.views',
    # Button Style URLs
    url(r'^client/(?P<client_pk>\d+)/button/$', 'button_views.button_list',
        name='button-list'),
    url(r'^client/(?P<client_pk>\d+)/button/(?P<pk>\d+)/$', 'button_views.button_detail',
        name='button-detail'),
    url(r'^client/(?P<client_pk>\d+)/button/new/$', 'button_views.button_edit',
        name='button-new'),
    url(r'^client/(?P<client_pk>\d+)/button/edit/(?P<pk>\d+)/$', 'button_views.button_edit',
        name='button-edit'),
)

urlpatterns += patterns('targetadmin.views',
    # Campaign URLs
    url(r'^client/(?P<client_pk>\d+)/campaign/$', 'campaign_views.campaign_list',
        name='campaign-list'),
    url(r'^client/(?P<client_pk>\d+)/campaign/(?P<pk>\d+)/$', 'campaign_views.campaign_detail',
        name='campaign-detail'),
    url(r'^client/(?P<client_pk>\d+)/campaign/new/$', 'campaign_views.campaign_create',
        name='campaign-new'),
    url(r'^client/(?P<client_pk>\d+)/campaign/wizard/$', 'campaign_views.campaign_wizard',
        name='campaign-wizard'),
    url(r'^client/(?P<client_pk>\d+)/campaign/wizard/(?P<campaign_pk>\d+)/(?P<content_pk>\d+)/finish/$',
        'campaign_views.campaign_wizard_finish',
        name='campaign-wizard-finish'),
    url(r'^client/(?P<client_pk>\d+)/spiking/$', 'campaign_views.spiking',
        name='spiking'),
)

urlpatterns += patterns('targetadmin.views',
    # Snippet URLs
    url(r'^client/(?P<client_pk>\d+)/snippets/$', 'snippets.snippets',
        name='snippets'),
    url(r'^client/(?P<client_pk>\d+)/snippet-update/$',
        'snippets.snippet_update',
        name='snippet-update')
)

urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', name='login'),
)
