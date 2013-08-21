from django.conf.urls import patterns, url
from django.views.generic import ListView, DetailView

from targetshare.models import relational
from targetadmin import utils


urlpatterns = patterns('targetadmin.views',
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
    url(r'^client/(?P<client_pk>\d+)/content/$', 'content_list',
        name='content-list'),
    url(r'^client/(?P<client_pk>\d+)/content/(?P<pk>\d+)/$', 'content_detail',
        name='content-detail'),
    url(r'^client/(?P<client_pk>\d+)/content/new/$', 'content_edit',
        name='content-new'),
    url(r'^client/(?P<client_pk>\d+)/content/edit/(?P<pk>\d+)/$', 'content_edit',
        name='content-edit'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/$', 'fb_object_list',
        name='fb-obj-list'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/(?P<pk>\d+)/$', 'fb_object_detail',
        name='fb-obj-detail'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/new/$', 'fb_object_edit',
        name='fb-obj-new'),
    url(r'^client/(?P<client_pk>\d+)/fbobject/edit/(?P<pk>\d+)/$', 'fb_object_edit',
        name='fb-obj-edit'),
)

urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', name='login'),
)
