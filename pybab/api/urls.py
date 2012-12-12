from django.conf.urls import patterns, url#, include

urlpatterns = patterns('pybab.api',
#    url(r'^styles/$', 'views.upload_style'),
#    url(r'^styles/delete/(?P<pk>\d+)/$', 'views.delete_style'),
    # catalog layer
    url(r'^layer/$', 'views.catalog_layer'),
    url(r'^layer/(?P<index>\d+)/$', 'views.catalog_layer'),
    #catalog statistical
    url(r'^statistical/$', 'views.catalog_statistical'),
    url(r'^statistical/(?P<index>\d+)/$', 'views.catalog_statistical'),
    #catalog indicator
    url(r'^indicator/$', 'views.catalog_indicator'),
    url(r'^indicator/(?P<index>\d+)/$', 'views.catalog_indicator'),
    #metadata
    url(r'^metadata/(?P<index>\d+)/$', 'views.metadata'),
)


from django.conf import settings
if getattr(settings, 'DEBUG', False):
    urlpatterns += patterns('',
                            url(r'layer/form/', 'pybab.api.views.new_layer_views.layer_form'))
