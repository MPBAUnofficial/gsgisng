from django.contrib import admin
from shp_uploader.models import UserStyle, UserLayer
from forms import ShapeForm

class UserLayerAdmin(admin.ModelAdmin):
    form = ShapeForm

class UserStyleAdmin(admin.ModelAdmin):
    exclude = ('name',)
    readonly_fields = ('name',)

admin.site.register(UserStyle, UserStyleAdmin)
admin.site.register(UserLayer, UserLayerAdmin)
