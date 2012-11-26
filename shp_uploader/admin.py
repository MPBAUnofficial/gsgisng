from django.contrib import admin
from shp_uploader.models import UserStyle, UserLayer

class UserLayerAdmin(admin.ModelAdmin):
    pass

class UserStyleAdmin(admin.ModelAdmin):
    exclude = ('name',)
    readonly_fields = ('name',)

admin.site.register(UserStyle, UserStyleAdmin)
admin.site.register(UserLayer, UserLayerAdmin)
