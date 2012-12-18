from django import forms
from .models import CatalogLayer, CatalogStatistical, CatalogIndicator
from pybab.models import LayerGroup, IndicatorGroup, StatisticalGroup

class LayerGroupForm(forms.ModelForm):
    parent = forms.ChoiceField()

    class Meta:
        fields = ("name", )
        model = LayerGroup

    def clean_parent(self):
        parent_id = self.cleaned_data['parent']
        parent = LayerGroup.objects.filter(pk=parent_id).get()
        return parent

    def save(self, force_insert=False, force_update=False, commit=True):
        layer_group = super(LayerGroupForm, self).save(commit=False)
        layer_group.save()
        layer_group.parent = self.cleaned_data['parent']
        return layer_group

class IndicatorGroupForm(forms.ModelForm):
    parent = forms.ChoiceField()

    class Meta:
        fields = ("name", )
        model = IndicatorGroup

    def clean_parent(self):
        parent_id = self.cleaned_data['parent']
        parent = IndicatorGroup.objects.filter(pk=parent_id).get()
        return parent

    def save(self, force_insert=False, force_update=False, commit=True):
        indicator_group = super(IndicatorGroupForm, self).save(commit=False)
        indicator_group.save()
        indicator_group.parent = self.cleaned_data['parent']
        return indicator_group

class StatisticalGroupForm(forms.ModelForm):
    parent = forms.ChoiceField()

    class Meta:
        fields = ("name", )
        model = StatisticalGroup

    def clean_parent(self):
        parent_id = self.cleaned_data['parent']
        parent = StatisticalGroup.objects.filter(pk=parent_id).get()
        return parent

    def save(self, force_insert=False, force_update=False, commit=True):
        statistical_group = super(StatisticalGroupForm, self).save(commit=False)
        statistical_group.save()
        statistical_group.parent = self.cleaned_data['parent']
        return statistical_group

class CatalogLayerForm(forms.ModelForm):
    group = forms.ChoiceField()

    class Meta:
        exclude = ("group",)
        model = CatalogLayer

    def clean_group(self):
        group_id = self.cleaned_data['group']
        group = LayerGroup.objects.filter(pk=group_id).get()
        return group

    def save(self, force_insert=False, force_update=False, commit=True):
        catalog_layer = super(CatalogLayerForm, self).save(commit=False)
        catalog_layer.group = self.cleaned_data['group']
        if commit:
            catalog_layer.save()
        return catalog_layer

class CatalogIndicatorForm(forms.ModelForm):
    group = forms.ChoiceField()

    class Meta:
        exclude = ("group",)
        model = CatalogIndicator

    def clean_group(self):
        group_id = self.cleaned_data['group']
        group = IndicatorGroup.objects.filter(pk=group_id).get()
        return group

    def save(self, force_insert=False, force_update=False, commit=True):
        catalog_indicator = super(CatalogIndicatorForm, self).save(commit=False)
        catalog_indicator.group = self.cleaned_data['group']
        if commit:
            catalog_indicator.save()
        return catalog_indicator

class CatalogStatisticalForm(forms.ModelForm):
    group = forms.ChoiceField()

    class Meta:
        exclude = ("group",)
        model = CatalogStatistical

    def clean_group(self):
        group_id = self.cleaned_data['group']
        group = StatisticalGroup.objects.filter(pk=group_id).get()
        return group

    def save(self, force_insert=False, force_update=False, commit=True):
        catalog_statistical = super(CatalogStatisticalForm, self).save(commit=False)
        catalog_statistical.group = self.cleaned_data['group']
        if commit:
            catalog_statistical.save()
        return catalog_statistical
