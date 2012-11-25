from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('',
    url(r'^upload_shape/', 'shp_uploader.views.upload_shp'),
    url(r'^delete_shape/(?P<pk>\d+)/$', 'shp_uploader.views.delete_shp'),
    url(r'^list_shapes/', 'shp_uploader.views.list_shps'),
    url(r'^upload_style/', 'shp_uploader.views.upload_style'),
    url(r'^delete_style/(?P<pk>\d+)/$', 'shp_uploader.views.delete_style'),
    url(r'^list_styles/', 'shp_uploader.views.list_styles'),
)

if getattr(settings, 'DEBUG', False):
    urlpatterns += patterns('',
                            url(r'form/', 'shp_uploader.views.display'))
