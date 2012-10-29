from django.contrib import admin
from .models import *

admin.site.register(Point, type('PointAdmin', (admin.ModelAdmin,), {}))
admin.site.register(Image, type('ImageAdmin', (admin.ModelAdmin,), {}))
admin.site.register(Document, type('DocumentAdmin', (admin.ModelAdmin,), {}))
