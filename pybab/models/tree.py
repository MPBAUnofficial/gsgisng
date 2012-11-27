from django.contrib.gis.db import models
from django.db.models import Q
from .commons import AdditionalData, GeoTreeModel
from ..context_managers import get_raw_cursor

# ===========================================================================
# Element to Label link (with validity)
# ===========================================================================

class Attribute(GeoTreeModel):
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
        app_label = u'pybab'
        db_table = u'gt_attribute'
        managed=False

# ===========================================================================
# Element
# ===========================================================================

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


class Element(GeoTreeModel):
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
        app_label = u'pybab'
        db_table = u'gt_element'
        managed=False

class Tree(GeoTreeModel):
    id = models.AutoField(primary_key=True)
    gt_element = models.ForeignKey(Element, related_name="tree_elements")
    gt_parent = models.ForeignKey(Element, related_name="tree_parents")

    class Meta:
        app_label = u'pybab'
        db_table = u'gt_tree'
        managed=False

class Label(GeoTreeModel):
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
        app_label = u'pybab'
        db_table = u'gt_label'
        managed=False


