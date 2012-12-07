from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from .tree import Element
from .commons import GeoTreeModel, GeoTreeError, pg_run, dict_union

# ===========================================================================
# Utilities
# ===========================================================================

class CatalogModel(GeoTreeModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    creation_time = models.DateTimeField(auto_now_add=True)
    numcode = models.IntegerField(default=0)
    remotehost = models.CharField(max_length=255, null=True)
    remoteport = models.IntegerField(null=True)
    remotedb = models.CharField(max_length=255, null=True)
    remoteuser = models.CharField(max_length=255, null=True)
    remotepass = models.CharField(max_length=255, null=True)
    tableschema = models.TextField(null=True) 
    tablename = models.TextField(null=True) 
    code_column = models.TextField(null=True)
    time_column = models.TextField(null=True)
    
    @property
    def catalog_type(self):
        return type(self).__name__

    @property
    def elements(self):
        return Catalog.objects.get(pk=self.pk).elements
    
    def to_dict(self):
        return {'id':self.id,
                'name':self.name,
                'creation_time':self.creation_time.isoformat(),
                'numcode':self.numcode,
                'remotehost':self.remotehost,
                'remoteport':self.remoteport,
                'remotedb':self.remotedb,
                'remoteuser':self.remoteuser,
                'remotepass':self.remotepass,
                'tableschema':self.tableschema,
                'tablename':self.tableschema,
                'code_column':self.code_column,
                'time_column':self.time_column}

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
    group = models.ForeignKey('IndicatorGroup', default=lambda:IndicatorGroup.objects.get(pk=0))
    data_column = models.TextField() 
    ui_palette = models.CharField(max_length=255, null=True)
    ui_quartili = models.TextField(null=True)
    gs_name = models.CharField(max_length=255)
    gs_workspace = models.CharField(max_length=255, null=True)
    gs_url = models.CharField(max_length=255)

    def to_json(self):
        dict_temp = { 'data_column': self.data_column,
                      'ui_palette':self.ui_palette,
                      'ui_quartili':self.ui_quartili,
                      'gs_name':self.gs_name,
                      'gs_workspace':self.gs_workspace,
                      'gs_url':self.url}
        
        return dict_union(dict_temp,super(CatalogIndicator,self).to_json())
    
    class Meta(CatalogModel.Meta):
        db_table = u'gt_catalog_indicator'
        
class IndicatorGroup(GroupModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    
    def to_json(self):
        return {'id':self.id,
                'name':self.name}
    
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
    group = models.ForeignKey('StatisticalGroup', default=lambda:StatisticalGroup.objects.get(pk=0))
    data_column = models.TextField() 
    
    def to_json(self):
        dict_temp = { 'data_column': self.data_column}
        return dict_union(dict_temp,super(CatalogIndicator,self).to_json())

    class Meta(CatalogModel.Meta):
        db_table = u'gt_catalog_statistical'

class StatisticalGroup(GroupModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    
    def to_json(self):
        return {'id':self.id,
                'name':self.name}

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
    group = models.ForeignKey('LayerGroup', default=lambda:LayerGroup.objects.get(pk=0))
    geom_column = models.TextField(null=True)
    ui_qtip = models.CharField(max_length=255, null=True)
    gs_name = models.CharField(max_length=255,
                               verbose_name=_(u"Geoserver layer name"))
    gs_workspace = models.CharField(max_length=255, null=True)
    gs_url = models.CharField(max_length=255)
    gs_legend_url = models.CharField(max_length=255, null=True)

    def import_elements_from(self, name_column, parent_column, elements_rank):
        if self.tablename is None or self.tablename == "":
            raise GeoTreeError("Can't import layer into catalog because tablename is not defined.")
        proc_name = u'gt_layer_import'
        args = [self.pk, name_column, parent_column, elements_rank]
        return pg_run(proc_name, args)

    def to_json(self):
        dict_temp = { 'geom_column': self.geom_column,
                      'ui_tip':self.ui_tip,
                      'gs_name':self.gs_name,
                      'gs_workspace':self.gs_workspace,
                      'gs_url':self.gs_url,
                      'gs_legend_url':self.gs_legend_url}

        return dict_union(dict_temp,super(CatalogIndicator,self).to_json())

    class Meta(CatalogModel.Meta):
        db_table=u'gt_catalog_layer'

class LayerGroup(GroupModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    
    def to_json(self):
        return {'id':self.id,
                'name':self.name}

    class Meta(GroupModel.Meta):
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
    remotehost = models.CharField(max_length=255, null=True)
    remoteport = models.IntegerField(null=True)
    remotedb = models.CharField(max_length=255, null=True)
    remoteuser = models.CharField(max_length=255, null=True)
    remotepass = models.CharField(max_length=255, null=True)
    tableschema = models.TextField(null=True) 
    tablename = models.TextField(null=True) 
    code_column = models.TextField(null=True)
    time_column = models.TextField(null=True)

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
    
    def to_dict(self):
        return {'id':self.id,
                'name':self.name,
                'creation_time':self.creation_time.isoformat(),
                'numcode':self.numcode,
                'remotehost':self.remotehost,
                'remoteport':self.remoteport,
                'remotedb':self.remotedb,
                'remoteuser':self.remoteuser,
                'remotepass':self.remotepass,
                'tableschema':self.tableschema,
                'tablename':self.tableschema,
                'code_column':self.code_column,
                'time_column':self.time_column}

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
    title = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    category = models.TextField(null=True)
    extent = models.TextField(null=True)
    measure_unit = models.TextField(null=True)
    author = models.TextField(null=True)
    ref_year = models.IntegerField(null=True)
    creation_year = models.IntegerField(null=True)
    native_format = models.TextField(null=True)
    genealogy = models.TextField(null=True)
    spatial_resolution = models.TextField(null=True)
    ref_system = models.TextField(null=True)
    availability = models.TextField(null=True)
    has_attributes = models.NullBooleanField(null=True)
    source = models.TextField(null=True)
         
    def to_dict(self):
        return {'id':self.id,
                'title':self.title,
                'description':self.description,
                'category':self.category,
                'extent':self.extent,
                'measure_unit':self.measure_unit,
                'author':self.author,
                'ref_year':self.ref_year,
                'creation_year':self.creation_year,
                'native_format':self.native_format,
                'genealogy':self.genealogy,
                'spatial_resolution':self.spatial_resolution,
                'ref_system':self.ref_system,
                'availability':self.availability,
                'has_attributes':self.has_attributes,
                'source':self.source}

    class Meta(GeoTreeModel.Meta):
        db_table = u'gt_meta'
