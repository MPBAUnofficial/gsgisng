from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from .tree import Element
from .commons import GeoTreeModel, GeoTreeError, pg_run

# ===========================================================================
# Utilities
# ===========================================================================

class CatalogModel(GeoTreeModel):
    @property
    def catalog_type(self):
        return type(self).__name__

    @property
    def elements(self):
        return Catalog.objects.get(pk=self.pk).elements

    def __unicode__(self):
        return u'({id}, {name})'.format(id=self.id, name=self.name)

    class Meta(GeoTreeModel.Meta):
        abstract=True

class GroupModel(GeoTreeModel):
    ROOT_ID = 0
    @property
    def is_root(self):
        return self.pk == GroupModel.ROOT_ID

    @property
    def parent(self):
        if self.is_root:
            return None
        else:
            return type(self).objects.get(parent_tree__group=self)

    @property
    def children(self):
        return type(self).objects.filter(child_tree__parent_group=self).exclude(
                pk=GroupModel.ROOT_ID)

    def to_dict(self):
        return {'id':self.id,
                'name':self.name,
                'leaf':False}

    def __unicode__(self):
        return u'({id}, {name})'.format(id=self.id, name=self.name)

    class Meta(GeoTreeModel.Meta):
        abstract=True

# ===========================================================================
# Catalog to Element link
# ===========================================================================

class ElementCatalogLink(GeoTreeModel):
    id = models.AutoField(primary_key=True)
    gt_element = models.ForeignKey(Element, related_name="catalog_link_elements")
    gt_catalog_id = models.ForeignKey('Catalog')

    class Meta(GeoTreeModel.Meta):
        db_table = u'gt_element_catalog_link'

# ===========================================================================
# Catalog Indicator
# ===========================================================================

class CatalogIndicator(CatalogModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    creation_time = models.DateTimeField(auto_now_add=True)
    numcode = models.IntegerField(default=0)
    remotehost = models.CharField(max_length=255, blank=True, null=True)
    remoteport = models.IntegerField(null=True, blank=True)
    remotedb = models.CharField(max_length=255, blank=True, null=True)
    remoteuser = models.CharField(max_length=255, blank=True, null=True)
    remotepass = models.CharField(max_length=255, blank=True, null=True)
    tableschema = models.TextField() 
    tablename = models.TextField() 
    group = models.ForeignKey('IndicatorGroup', default=lambda:IndicatorGroup.objects.get(pk=0))
    code_column = models.TextField() 
    data_column = models.TextField() 
    time_column = models.TextField(blank=True, null=True) 
    ui_palette = models.CharField(max_length=255, blank=True, null=True)
    ui_quartili = models.TextField(blank=True, null=True)
    gs_name = models.CharField(max_length=255)
    gs_workspace = models.CharField(max_length=255, blank=True, null=True)
    gs_url = models.CharField(max_length=255)

    class Meta(CatalogModel.Meta):
        db_table = u'gt_catalog_indicator'
        
class IndicatorGroup(GroupModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    
    class Meta(GroupModel.Meta):
        db_table = u'gt_indicator_group'

class IndicatorTree(GeoTreeModel):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(IndicatorGroup, unique=True, related_name='child_tree')
    parent_group = models.ForeignKey(IndicatorGroup, related_name='parent_tree')
    class Meta(GeoTreeModel.Meta):
        db_table = u'gt_indicator_tree'

# ===========================================================================
# Catalog Statistical
# ===========================================================================

class CatalogStatistical(CatalogModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    creation_time = models.DateTimeField(auto_now_add=True)
    numcode = models.IntegerField(default=0)
    remotehost = models.CharField(max_length=255, blank=True)
    remoteport = models.IntegerField(null=True, blank=True)
    remotedb = models.CharField(max_length=255, blank=True, null=True)
    remoteuser = models.CharField(max_length=255, blank=True, null=True)
    remotepass = models.CharField(max_length=255, blank=True, null=True)
    tableschema = models.TextField() # This field type is a guess.
    tablename = models.TextField() # This field type is a guess.
    group = models.ForeignKey('StatisticalGroup', default=lambda:StatisticalGroup.objects.get(pk=0))
    code_column = models.TextField() # This field type is a guess.
    data_column = models.TextField() # This field type is a guess.
    time_column = models.TextField(blank=True, null=True) # This field type is a guess.

    class Meta(CatalogModel.Meta):
        db_table = u'gt_catalog_statistical'

class StatisticalGroup(GroupModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta(GroupModel.Meta):
        db_table = u'gt_statistical_group'

class StatisticalTree(GeoTreeModel):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(StatisticalGroup, unique=True, related_name='child_tree')
    parent_group = models.ForeignKey(StatisticalGroup, related_name='parent_tree')

    class Meta(GeoTreeModel.Meta):
        db_table = u'gt_statistical_tree'

# ===========================================================================
# Catalog Layer
# ===========================================================================

class CatalogLayer(CatalogModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    creation_time = models.DateTimeField(auto_now_add=True)
    numcode = models.IntegerField(default=0)
    remotehost = models.CharField(max_length=255, blank=True, null=True)
    remoteport = models.IntegerField(null=True, blank=True)
    remotedb = models.CharField(max_length=255, blank=True, null=True)
    remoteuser = models.CharField(max_length=255, blank=True, null=True)
    remotepass = models.CharField(max_length=255, blank=True, null=True)
    tableschema = models.TextField(blank=True, null=True)
    tablename = models.TextField(blank=True, null=True) 
    group = models.ForeignKey('LayerGroup', default=lambda:LayerGroup.objects.get(pk=0))
    code_column = models.TextField(blank=True, null=True) 
    time_column = models.TextField(blank=True, null=True)
    geom_column = models.TextField(blank=True, null=True)
    ui_qtip = models.CharField(max_length=255, blank=True, null=True)
    gs_name = models.CharField(max_length=255,
                               verbose_name=_(u"Geoserver layer name"))
    gs_workspace = models.CharField(max_length=255, blank=True, null=True)
    gs_url = models.CharField(max_length=255)
    gs_legend_url = models.CharField(max_length=255, blank=True, null=True)

    def import_elements_from(self, name_column, parent_column, elements_rank):
        if self.tablename is None or self.tablename == "":
            raise GeoTreeError("Can't import layer into catalog because tablename is not defined.")
        proc_name = u'gt_layer_import'
        args = [self.pk, name_column, parent_column, elements_rank]
        return pg_run(proc_name, args)

    class Meta(CatalogModel.Meta):
        db_table=u'gt_catalog_layer'

class LayerGroup(GeoTreeModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta(GeoTreeModel.Meta):
        db_table=u'gt_layer_group'

class LayerTree(GroupModel):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(LayerGroup, unique=True, related_name="child_tree")
    parent_group = models.ForeignKey(LayerGroup, related_name="parent_tree")

    class Meta(GroupModel.Meta):
        db_table=u'gt_layer_tree'

# ===========================================================================
# Catalog
# ===========================================================================

class Catalog(GeoTreeModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    creation_time = models.DateTimeField(auto_now_add=True)
    numcode = models.IntegerField(default=0)
    remotehost = models.CharField(max_length=255, blank=True, null=True)
    remoteport = models.IntegerField(null=True, blank=True)
    remotedb = models.CharField(max_length=255, blank=True, null=True)
    remoteuser = models.CharField(max_length=255, blank=True, null=True)
    remotepass = models.CharField(max_length=255, blank=True, null=True)
    tableschema = models.TextField(blank=True, null=True) # This field type is a guess.
    tablename = models.TextField(blank=True, null=True) # This field type is a guess.
    code_column = models.TextField(blank=True, null=True)
    time_column = models.TextField(blank=True, null=True)

    @property
    def specific(self):
        if self.pk == 0:
            return self

        subtables = [CatalogStatistical, CatalogLayer, CatalogIndicator]
        for subtable in subtables:
            try:
                return subtable.objects.get(pk=self.pk)
            except subtable.DoesNotExist:
                continue

    def save(self, force_insert=False, force_update=False):
        raise GeoTreeError("Can not update gt_catalog directly")

    def delete(self):
        raise GeoTreeError("Can not delete from gt_catalog directly")

    def __unicode__(self):
        return self.name

    class Meta(GeoTreeModel.Meta):
        db_table = u'gt_catalog'

# ===========================================================================
# Catalog
# ===========================================================================

class Meta(GeoTreeModel):
    id = models.AutoField(primary_key=True)
    gt_catalog = models.ForeignKey(Catalog, unique=True, related_name="metadata_set")
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    measure_unit = models.TextField(blank=True, null=True)
    class Meta(GeoTreeModel.Meta):
        db_table = u'gt_meta'
