from django.conf.urls import patterns, url
from django.core.exceptions import PermissionDenied
from django.contrib.auth import decorators
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
    url(r'^client/new/$', 'edit_client', name='client-new'),
    url(r'^client/edit/(?P<client_pk>\d+)/$', 'edit_client', name='client-edit'),
)

urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', name='login'),
)
