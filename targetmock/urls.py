from django.conf.urls import patterns, url
from django.views.generic.base import TemplateView

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='targetmock/index.html'),
        name='mock-landing'),
    url(r'^guncontrol/$',
        TemplateView.as_view(template_name='targetmock/mayors_share_wrapper.html'),
         name='mayors-auth'),
    url(r'^guncontrol_share/$',
        TemplateView.as_view(template_name='targetmock/mayors_faces_wrapper.html'),
        name='mayors-share'),
    url(r'^immigration/$',
        TemplateView.as_view(template_name='targetmock/immigration_share_wrapper.html'),
        name='immigration-auth'),
    url(r'^immigration_share/$',
        TemplateView.as_view(template_name='targetmock/immigration_faces_wrapper.html'),
         name='immigration-share'),
    url(r'^ofa/$',
        TemplateView.as_view(template_name='targetmock/ofa_share_wrapper.html'),
         name='ofa-auth'),
    url(r'^ofa_share/$',
        TemplateView.as_view(template_name='targetmock/ofa_faces_wrapper.html'),
         name='ofa-share'),
    url(r'^baron/$',
        TemplateView.as_view(template_name='targetmock/faces_wrapper.html'),
         name='default'),
)


urlpatterns += patterns('targetmock.views',
    url(r'^ofa_landing/$', 'ofa_landing', name='ofa-landing'),
)
