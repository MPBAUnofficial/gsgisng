from django.conf.urls import patterns, url#, include

urlpatterns = patterns('pybab.api',
#    url(r'^styles/$', 'views.upload_style'),
#    url(r'^styles/delete/(?P<pk>\d+)/$', 'views.delete_style'),
    # catalog layer
    url(r'^layer/(?P<index>\d+)/$', 'views.catalog_layer'),
    #catalog statistical
    url(r'^statistical/(?P<index>\d+)/$', 'views.catalog_statistical'),
    #catalog indicator
    url(r'^indicator/(?P<index>\d+)/$', 'views.catalog_indicator'),
)
