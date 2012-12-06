from django.conf.urls import patterns, url#, include
from django.conf import settings

urlpatterns = patterns('pybab.api',
    #catalogLayer
    url(r'^layers/$', 'views.upload_layer'),
    url(r'^layers/delete/(?P<pk>\d+)/$', 'views.delete_layer'),
    url(r'^styles/$', 'views.upload_style'),
    url(r'^styles/delete/(?P<pk>\d+)/$', 'views.delete_style'),
    #catalogStatistical
    url(r'^statistical/(?P<tree_index>\d+)/$', 'views.catalog_statistical'),
    #catalogIndicator
    url(r'^indicator/(?P<tree_index>\d+)/$', 'views.catalog_indicator'),
)

if getattr(settings, 'DEBUG', False):
    urlpatterns += patterns('pybab.api',
                            url(r'^layers/list', 'views.layer_views.list_layers'),
                            url(r'^styles/list', 'views.list_styles'),
                            url(r'form_layer/', 'views.layer_form'))
