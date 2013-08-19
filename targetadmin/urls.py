from django.conf.urls import patterns, url
from django.core.exceptions import PermissionDenied
from django.contrib.auth import decorators
from django.views.generic import ListView, DetailView

from targetshare.models import relational


def superuser_required(view):
    def check_superuser(user):
        if user.is_superuser:
            return True
        raise PermissionDenied
    return decorators.user_passes_test(check_superuser)(view)


def internal(view):
    is_superuser = superuser_required(view)
    logged_in_superuser = decorators.login_required(is_superuser, login_url='login')
    return logged_in_superuser


urlpatterns = patterns('targetadmin.views',
    url(r'^$', internal(
        ListView.as_view(
            model=relational.Client,
            template_name='targetadmin/home.html'
        )),
        name='client-list'),
    url(r'^client/(?P<pk>\d+)/$', internal(
        DetailView.as_view(
            model=relational.Client,
            template_name='targetadmin/client_home.html'
        )),
        name='client-detail'),
)

urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', name='login'),
)
