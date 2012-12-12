from django.db import models
from django.db.models import Q

from .exceptions import GeoTreeError
from .context_managers import get_raw_cursor

class GeoTree(object):
    def is_geotree():
        tables = [u'gt_attribute',
                  u'gt_catalog',
                  u'gt_catalog_indicator',
                  u'gt_catalog_layer',
                  u'gt_cagalog_statistics',
                  u'gt_element',
                  u'gt_element_catalog',
                  u'gt_label',
                  u'gt_meta',
                  u'gt_tree']

        with get_raw_cursor() as cursor:
            for table in tables:
                try:
                    cursor.execute("SELECT * FROM %s;", table)
                except:
                    return False

        return True

    @property
    def Element(self):
        return Element

    @property
    def Label(self):
        return Label

    @property
    def root(self):
        return self.Element.objects.get(code='root')

    @property
    def fakeroot(self):
        return self.Element.objects.get(code='fakeroot')

class CatalogMixin(object):
    @property
    def catalog_type(self):
        return type(self).__name__

    @property
    def elements(self):
        return Catalog.objects.get(pk=self.pk).elements

    def __unicode__(self):
        return self.name

class AdditionalData(object):
    def __init__(self):
        self.attributes = []

    def add(self, name, value):
        setattr(self, name, value)

    def __setattr__(self, name, value):
        if name != "attributes":
            self.attributes.append(name)
        super(AdditionalData, self).__setattr__(name, value)


class ElementCatalogLink(models.Model):
    id = models.AutoField(primary_key=True)
    gt_element = models.ForeignKey('Element', related_name="catalog_link_elements")
    gt_catalog = models.ForeignKey('Catalog')
    class Meta:
        db_table = u'gt_element_catalog_link'
        managed=False

class Attribute(models.Model):
    id = models.AutoField(primary_key=True)
    gt_element = models.ForeignKey('Element')
    gt_label = models.ForeignKey('Label')
    timestart = models.DateTimeField()
    timeend = models.DateTimeField()

    @staticmethod
    def _filter_by_date(queryset, time_start=None, time_end=None):
        if time_start and time_end:
            return queryset.filter(Q(timestart__lte=time_start),Q(timeend__gte=time_end))
        elif time_start:
            return queryset.filter(timestart__lte=time_start)
        elif time_end:
            return queryset.filter(timeend__gte=time_end)
        else:
            return queryset.all()

    def __unicode__(self):
        return u"{}, {}".format(
                self.timestart.isoformat(),
                self.timeend.isoformat())

    class Meta:
        db_table = u'gt_attribute'
        managed=False

class CatalogIndicator(models.Model, CatalogMixin):
    id = models.AutoField(primary_key=True)
    id_padre = models.BigIntegerField()
    name = models.CharField(max_length=255)
    leaf = models.BooleanField()
    numcode = models.IntegerField(null=True, blank=True)
    tableschema = models.TextField() # This field type is a guess.
    tablename = models.TextField() # This field type is a guess.
    code_column = models.TextField() # This field type is a guess.
    data_column = models.TextField() # This field type is a guess.
    time_column = models.TextField(blank=True) # This field type is a guess.
    geom_column = models.TextField(blank=True) # This field type is a guess.
    ui_checked = models.BooleanField()
    ui_palette = models.CharField(max_length=255, blank=True)
    ui_quartili = models.TextField(blank=True)
    gs_name = models.CharField(max_length=255)
    gs_workspace = models.CharField(max_length=255, blank=True)
    gs_url = models.CharField(max_length=255)

    class Meta:
        db_table = u'gt_catalog_indicator'
        managed=False

class CatalogStatistical(models.Model, CatalogMixin):
    id = models.AutoField(primary_key=True)
    id_padre = models.BigIntegerField()
    name = models.CharField(max_length=255)
    leaf = models.BooleanField()
    numcode = models.IntegerField(null=True, blank=True)
    tableschema = models.TextField() # This field type is a guess.
    tablename = models.TextField() # This field type is a guess.
    code_column = models.TextField() # This field type is a guess.
    data_column = models.TextField() # This field type is a guess.
    time_column = models.TextField(blank=True) # This field type is a guess.
    geom_column = models.TextField(blank=True) # This field type is a guess.

    class Meta:
        db_table = u'gt_catalog_statistical'
        managed=False

class CatalogLayer(models.Model, CatalogMixin):
    id = models.AutoField(primary_key=True)
    id_padre = models.BigIntegerField()
    name = models.CharField(max_length=255)
    leaf = models.BooleanField()
    numcode = models.IntegerField(null=True, blank=True)
    tableschema = models.TextField(blank=True) # This field type is a guess.
    tablename = models.TextField(blank=True) # This field type is a guess.
    code_column = models.TextField(blank=True) # This field type is a guess.
    data_column = models.TextField(blank=True) # This field type is a guess.
    time_column = models.TextField(blank=True) # This field type is a guess.
    geom_column = models.TextField(blank=True) # This field type is a guess.
    ui_checked = models.BooleanField()
    ui_qtip = models.CharField(max_length=255, blank=True)
    gs_name = models.CharField(max_length=255, blank=True)
    gs_workspace = models.CharField(max_length=255, blank=True)
    gs_url = models.CharField(max_length=255, blank=True)
    gs_legend_url = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = u'gt_catalog_layer'
        managed=False

class Catalog(models.Model):
    id = models.AutoField(primary_key=True)
    id_padre = models.BigIntegerField(default=0)
    name = models.CharField(max_length=255)
    leaf = models.BooleanField()
    numcode = models.IntegerField(null=True, blank=True)
    tableschema = models.TextField(blank=True) # This field type is a guess.
    tablename = models.TextField(blank=True) # This field type is a guess.
    code_column = models.TextField(blank=True) # This field type is a guess.
    data_column = models.TextField(blank=True) # This field type is a guess.
    time_column = models.TextField(blank=True) # This field type is a guess.
    geom_column = models.TextField(blank=True) # This field type is a guess.

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

    class Meta:
        db_table = u'gt_catalog'
        managed=False

class Meta(models.Model):
    id = models.AutoField(primary_key=True)
    gt_catalog = models.ForeignKey(Catalog, unique=True)
    description = models.TextField(blank=True)
    source = models.TextField(blank=True)
    measure_unit = models.TextField(blank=True)
    class Meta:
        db_table = u'gt_meta'
        managed=False

class ElementManager(models.Manager):
    def by_label(self, label):
        return label.elements.all()

    def by_labels(self, labels, strict=False):
        proc_name = u'gt_elements_by_labels' if not strict else u'gt_elements_by_labels_strict'
        args = [label.name for label in labels]
        with get_raw_cursor() as cursor:
            cursor.callproc(proc_name, args)
            result = [res[0] for res in cursor.fetchall()]

        return super(ElementManager, self).get_query_set().filter(code__in=result)


class Element(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    rank = models.FloatField()
    
    parents = models.ManyToManyField("self", through="Tree", symmetrical=False, related_name="children")
    labels = models.ManyToManyField("Label", through="Attribute", related_name="elements", symmetrical=False)
    catalogs = models.ManyToManyField("Catalog", through="ElementCatalogLink", related_name="elements", symmetrical=False)

    objects = ElementManager()

    def labels_with_validity(self, time_start=None, time_end=None):
        attrs = Attribute._filter_by_date(self.attribute_set, time_start, time_end)
        labels = []
        for attribute in attrs:
            label = attribute.gt_label
            setattr(label, 'additional_data', AdditionalData())
            label.additional_data.add('time_start', attribute.timestart)
            label.additional_data.add('time_end', attribute.timeend)
            labels.append(label)

        return labels

    def attach_child(self, child):
        link = Tree(gt_element=child, gt_parent=self)
        link.save()

    def attach_parent(self, parent):
        link = Tree(gt_element=self, gt_parent=parent)
        link.save()

    def add_label(self, label, time_start=None, time_end=None):
        label.add_to_elements([self], time_start, time_end)

    def __unicode__(self):
        return u"({name}, {code}, {rank})".format(name=self.name, code=self.code, rank=self.rank)

    def is_leaf(self):
        return len(self.children.all()) == 0

    class Meta:
        db_table = u'gt_element'
        managed=False


class Tree(models.Model):
    id = models.AutoField(primary_key=True)
    gt_element = models.ForeignKey(Element, related_name="tree_elements")
    gt_parent = models.ForeignKey(Element, related_name="tree_parents")

    class Meta:
        db_table = u'gt_tree'
        managed=False

class Label(models.Model):
    """
    TODO: Get labels with validity
    """

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def add_to_elements(self, elements, time_start=None, time_end=None):
        proc_name = u'gt_elements_add_label'
        element_codes = [element.code for element in elements]
        with get_raw_cursor() as cursor:
            if time_start is None and time_end is None:
                cursor.callproc(proc_name, [element_codes, self.name])
            else:
                cursor.callproc(proc_name, [element_codes, self.name, time_start, time_end])

            result = cursor.fetchone()

        return result

    def remove_from_elements(self, elements):
        proc_name = 'gt_elements_remove_label'
        element_codes = [element.code for element in elements]
        with get_raw_cursor() as cursor:
            cursor.callproc(proc_name, [element_codes, self.name])
            result = cursor.fetchone()

        return result

    def elements_with_validity(self, time_start=None, time_end=None):
        attrs = Attribute._filter_by_date(self.attribute_set, time_start, time_end) 
        elements = []
        for attribute in attrs:
            element = attribute.gt_element
            setattr(element, 'additional_data', AdditionalData())
            element.additional_data.add('time_start', attribute.timestart)
            element.additional_data.add('time_end', attribute.timeend)
            elements.append(element)

        return elements

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = u'gt_label'
        managed=False


