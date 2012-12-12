from django.contrib import admin

from .models import Element, CatalogLayer, CatalogStatistical, CatalogIndicator

admin.site.register(Element)
admin.site.register(CatalogLayer)
admin.site.register(CatalogStatistical)
admin.site.register(CatalogIndicator)
