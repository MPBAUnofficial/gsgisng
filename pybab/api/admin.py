from django import forms
from django.contrib import admin
from pybab.api.models import UserStyle, CatalogShape
from pybab.api.models import UserStatisticalLink
from forms import ShapeForm, UserStyleForm
from pybab.models import CatalogLayer

class AdminStyleForm(UserStyleForm):
    is_public = forms.BooleanField(label="Public", required=False)

    def save(self, force_insert=False, force_update=False, commit=True):
        userStyle = super(AdminStyleForm, self).save(commit=False)

        if self.cleaned_data['is_public']:
            userStyle.user = None
        else:
            userStyle.user = self.current_user

        if commit:
            userStyle.save()
        return userStyle

class CatalogShapeAdmin(admin.ModelAdmin):
    form = ShapeForm
    readonly_fields = ('gs_name',)

class UserStyleAdmin(admin.ModelAdmin):
    form = AdminStyleForm
    readonly_fields = ('name',)

    def get_form(self, request, obj=None, **kwargs):
         form = super(UserStyleAdmin, self).get_form(request, obj, **kwargs)
         form.current_user = request.user
         return form

admin.site.register(UserStyle, UserStyleAdmin)
admin.site.register(CatalogShape, CatalogShapeAdmin)

admin.site.register(UserStatisticalLink)
