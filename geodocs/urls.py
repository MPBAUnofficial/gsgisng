from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('geodocs.views',
    url(r'^new/$', 'new'),
    url(r'^getinfo/(?P<pk>\d+)/$', 'getinfo'),
    url(r'^delete/(?P<pk>\d+)/$', 'point_del'),
)

if getattr(settings, 'DEBUG', False):
    urlpatterns += patterns('geodocs.views',
                            url(r'form/', 'display'))
