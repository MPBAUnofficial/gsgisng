from .base import *
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
