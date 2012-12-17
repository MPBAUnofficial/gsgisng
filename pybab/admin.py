from django.contrib import admin
from forms import NodeChoiceField
from .models import Element, CatalogLayer, CatalogStatistical, CatalogIndicator, LayerGroup

class CatalogChangeList(ChangeList):
    def get_query_set(self, request=None):
        qs = super(CatalogChangeList, self).get_query_set(request)

        # always order by (tree_id, left)
        #trova qualche tipo di ordinamento
        return qs#.order_by(tree_id, left)


class CatalogModelAdmin(ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        dict(form_class=NodeChoiceField,
             queryset=db_field.rel.to.objects.all(),
             required=False)
        defaults.update(kwargs)
        kwargs = defaults
        return super(CatalogModelAdmin, self).\
            formfield_for_foreignkey(db_field,
                                     request,
                                     **kwargs)

    def get_changelist(self, request, **kwargs):
        return CatalogChangeList

admin.site.register(Element)
admin.site.register(CatalogLayer)
admin.site.register(CatalogStatistical)
admin.site.register(CatalogIndicator)
admin.site.register(LayerGroup, CatalogModelAdmin)
