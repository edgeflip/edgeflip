from django.conf.urls import patterns, url
from django.views.generic import ListView

from targetshare.models import relational


urlpatterns = patterns('targetadmin.views',
    (r'^$', ListView.as_view(model=relational.Client, template_name='targetadmin/home.html')),
)
