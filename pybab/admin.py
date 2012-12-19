from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from .forms import LayerGroupForm, IndicatorGroupForm, StatisticalGroupForm
from .forms import CatalogLayerForm, CatalogIndicatorForm, CatalogStatisticalForm
from django import forms
from .models import Element, CatalogLayer, CatalogStatistical, CatalogIndicator
from .models import LayerGroup, IndicatorGroup, StatisticalGroup

class LayerChangeList(ChangeList):
    def results(self):
        return LayerGroup.objects.tree_sorted_levels()

class LayerGroupAdmin(admin.ModelAdmin):
    form = LayerGroupForm

    def get_changelist(self,request, **kwargs):
        return LayerChangeList

    def get_form(self, request, obj=None, **kwargs):
        form = super(LayerGroupAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['parent'].choices=\
            LayerGroup.objects.subtree_sorted_indented(
                parent=LayerGroup.objects.get(id=LayerGroup.ROOT_ID),
                to_exclude=(obj,)
                )
        if obj and obj.parent:
            form.base_fields['parent'].initial = obj.parent.id
        return form

class IndicatorChangeList(ChangeList):
    def results(self):
        return IndicatorGroup.objects.tree_sorted_levels()

class IndicatorGroupAdmin(admin.ModelAdmin):
    form = IndicatorGroupForm

    def get_changelist(self,request, **kwargs):
        return IndicatorChangeList

    def get_form(self, request, obj=None, **kwargs):
        form = super(IndicatorGroupAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['parent'].choices=\
            IndicatorGroup.objects.subtree_sorted_indented(
                parent=IndicatorGroup.objects.get(id=IndicatorGroup.ROOT_ID),
                to_exclude=(obj,)
                )
        if obj and obj.parent:
            form.base_fields['parent'].initial = obj.parent.id
        return form

class StatisticalChangeList(ChangeList):
    def results(self):
        return StatisticalGroup.objects.tree_sorted_levels()

class StatisticalGroupAdmin(admin.ModelAdmin):
    form = StatisticalGroupForm

    def get_changelist(self,request, **kwargs):
        return StatisticalChangeList

    def get_form(self, request, obj=None, **kwargs):
        form = super(StatisticalGroupAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['parent'].choices=\
            StatisticalGroup.objects.subtree_sorted_indented(
                parent=StatisticalGroup.objects.get(id=StatisticalGroup.ROOT_ID),
                to_exclude=(obj,)
                )
        if obj and obj.parent:
            form.base_fields['parent'].initial = obj.parent.id
        return form

class CatalogLayerAdmin(admin.ModelAdmin):
    form = CatalogLayerForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(CatalogLayerAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['group'].choices=\
            LayerGroup.objects.subtree_sorted_indented(
                parent=LayerGroup.objects.get(id=LayerGroup.ROOT_ID),
                )
        if obj:
            form.base_fields['group'].initial = obj.group
        return form

class CatalogStatisticalAdmin(admin.ModelAdmin):
    form = CatalogStatisticalForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(CatalogStatisticalAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['group'].choices=\
            StatisticalGroup.objects.subtree_sorted_indented(
                parent=StatisticalGroup.objects.get(id=StatisticalGroup.ROOT_ID),
                )
        if obj:
            form.base_fields['group'].initial = obj.group
        return form

class CatalogIndicatorAdmin(admin.ModelAdmin):
    form = CatalogIndicatorForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(CatalogIndicatorAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['group'].choices=\
            IndicatorGroup.objects.subtree_sorted_indented(
                parent=IndicatorGroup.objects.get(id=IndicatorGroup.ROOT_ID),
                )
        if obj:
            form.base_fields['group'].initial = obj.group
        return form

admin.site.register(Element)
admin.site.register(CatalogLayer, CatalogLayerAdmin)
admin.site.register(CatalogStatistical, CatalogStatisticalAdmin)
admin.site.register(CatalogIndicator, CatalogIndicatorAdmin)
admin.site.register(LayerGroup, LayerGroupAdmin)
admin.site.register(IndicatorGroup, IndicatorGroupAdmin)
admin.site.register(StatisticalGroup, StatisticalGroupAdmin)
