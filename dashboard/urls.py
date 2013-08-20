from django.conf.urls import patterns, url

urlpatterns = patterns('dashboard.views',
    url( r'^$', 'dashboard', name='dashboard'),
    url( r'^chartdata/$', 'chartdata', name='chartdata'),
    url( r'^mkdata/$', 'mkdata', name='mkdata'),
)

# for reasons i dont understand, this url has to be added like this
urlpatterns += patterns('',
    url(r'login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'logout/$', 'django.contrib.auth.views.logout', name='logout'),
)
