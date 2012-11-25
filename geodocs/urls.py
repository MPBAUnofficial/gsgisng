from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('geodocs.views',
    url(r'^new/$', 'new'),
    url(r'^getinfo/(?P<pk>\d+)/$', 'getinfo'),
    url(r'^delete/(?P<pk>\d+)/$', 'point_del'),
    url(r'^my-points/$', 'my_points'),
    url(r'^delete-image/(?P<url>.+)$', 'img_del'),
    url(r'^delete-doc/(?P<url>.+)$', 'doc_del'),

    # per mobile immagini singole
    url(r'^new-point/$', 'new_single'),
    url(r'^new-image/(?P<point_pk>\d+)/$', 'new_image'),
    #url(r'^new-doc/(?P<point_pk>\d+)/$', 'new_doc'),
    # si suppone che da mobile si possano mandare solo immagini
)



if getattr(settings, 'DEBUG', False):
    urlpatterns += patterns('geodocs.views',
                            url(r'form/', 'display'))
