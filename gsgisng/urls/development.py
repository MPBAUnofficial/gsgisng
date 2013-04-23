from .base import *

# urlpatterns += patterns('',
#     url(r'^webgis/', include('gswebgis.setup.urls')),
#     url(r'^api/', include('pybab.api.urls')),
#     url(r'^plr/', include('plrutils.urls')),
# )

url = patterns('',
   url(r'^webgis/', include('gswebgis.setup.urls')),
   url(r'^api/', include('pybab.api.urls')),
   url(r'^plr/', include('plrutils.urls')),
)
urlpatterns = url + urlpatterns

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
