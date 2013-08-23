from django.conf.urls import patterns, url
from django.views.generic import ListView, DetailView

from targetshare.models import relational
from targetadmin import utils


urlpatterns = patterns('targetadmin.views',
    # Client URLS
    url(r'^$', utils.internal(
        ListView.as_view(
            model=relational.Client,
            template_name='targetadmin/home.html'
        )),
        name='client-list'),
    url(r'^client/(?P<pk>\d+)/$', utils.internal(
        DetailView.as_view(
            model=relational.Client,
            template_name='targetadmin/client_home.html'
        )),
        name='client-detail'),
    url(r'^client/new/$', 'client_view', name='client-new'),
    url(r'^client/(?P<pk>\d+)/edit/$', 'client_view', name='client-edit'),
    # Content URLs
    url(r'^client/(?P<client_pk>\d+)/content/$', 'content_list',
        name='content-list'),
    url(r'^client/(?P<client_pk>\d+)/content/(?P<pk>\d+)/$', 'content_detail',
        name='content-detail'),
    url(r'^client/(?P<client_pk>\d+)/content/new/$', 'content_edit',
        name='content-new'),
    url(r'^client/(?P<client_pk>\d+)/content/edit/(?P<pk>\d+)/$', 'content_edit',
        name='content-edit'),
    # FB Object URLs
    url(r'^client/(?P<client_pk>\d+)/fbobject/$', 'fb_object_list',
        name='fb-obj-list'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/(?P<pk>\d+)/$', 'fb_object_detail',
        name='fb-obj-detail'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/new/$', 'fb_object_edit',
        name='fb-obj-new'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/edit/(?P<pk>\d+)/$', 'fb_object_edit',
        name='fb-obj-edit'),
    # Filter URLs
    url(r'^client/(?P<client_pk>\d+)/filter/$', 'filter_list',
        name='filter-list'),
    url(r'^client/(?P<client_pk>\d+)/filter/(?P<pk>\d+)/$', 'filter_detail',
        name='filter-detail'),
    url(r'^client/(?P<client_pk>\d+)/filter/new/$', 'filter_new',
        name='filter-new'),
    url(r'^client/(?P<client_pk>\d+)/filter/edit/(?P<pk>\d+)/$', 'filter_edit',
        name='filter-edit'),
    # Choice Set URLs
    url(r'^client/(?P<client_pk>\d+)/cs/$', 'cs_list',
        name='cs-list'),
    url(r'^client/(?P<client_pk>\d+)/cs/(?P<pk>\d+)/$', 'cs_detail',
        name='cs-detail'),
    url(r'^client/(?P<client_pk>\d+)/cs/new/$', 'cs_new',
        name='cs-new'),
    url(r'^client/(?P<client_pk>\d+)/cs/edit/(?P<pk>\d+)/$', 'cs_edit',
        name='cs-edit'),
    # Button Style URLs
    url(r'^client/(?P<client_pk>\d+)/button/$', 'button_list',
        name='button-list'),
    url(r'^client/(?P<client_pk>\d+)/button/(?P<pk>\d+)/$', 'button_detail',
        name='button-detail'),
    url(r'^client/(?P<client_pk>\d+)/button/new/$', 'button_edit',
        name='button-new'),
    url(r'^client/(?P<client_pk>\d+)/button/edit/(?P<pk>\d+)/$', 'button_edit',
        name='button-edit'),
)

urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', name='login'),
)
