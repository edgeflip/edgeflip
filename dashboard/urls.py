from django.conf.urls import patterns, url

urlpatterns = patterns('dashboard.views',
    url( r'^$', 'dashboard', name='dashboard'),
    url( r'^chartdata/$', 'chartdata', name='chartdata'),
    url( r'^logout/$', 'dashlogout', name='dashlogout'),
)

# for reasons i dont understand, this url has to be added like this
urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', 
        {'template_name':'dashboard/login.html'}, name='login'),
)
