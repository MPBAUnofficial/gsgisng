import urllib2

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver

from pybab.models import CatalogLayer
from pybab.api import layer_settings
from pybab.api.layer_lib.pg2geoserver import Pg2Geoserver
from pybab.api.layer_lib import shape_utils

def _instantiate_pg2geoserver():
    geoserver_url = layer_settings.GEOSERVER_URL
    username = layer_settings.GEOSERVER_USER
    password = layer_settings.GEOSERVER_PASSWORD
    return Pg2Geoserver(geoserver_url,username,password)

class UserStyle(models.Model):
    POLYGONS = "PL"
    LINES = "LI"
    POINTS = "PN"
    FEATURE_TYPES = {
        POLYGONS: "polygons",
        LINES: "lines",
        POINTS: "points",
        }

    #if None, the style is for all the users
    user = models.ForeignKey(User, null=True, blank=True,
                             help_text=_(u"Leave blank to assign this"
                                         " style to all the users"))
    name = models.CharField(max_length=200,
                            verbose_name=_(u"Geoserver style name"),
                            help_text=_(u"Automatically generated"))
    label = models.CharField(max_length=200, verbose_name=_(u"Style Name"))
    xml = models.TextField()
    feature_type = models.CharField(max_length=2,
                                    choices=FEATURE_TYPES.items())
    created_at = models.DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return self.label

    def as_dict(self):
        return {'pk': self.pk,
                'style_name': self.name,
                'label': self.label,
                'xml': self.xml,
                'feature_type': self.FEATURE_TYPES[self.feature_type],
                'created_at': str(self.created_at),
                }

    class Meta:
        app_label = u'api'

@receiver(pre_delete, sender=UserStyle)
def style_delete_handler(sender, **kwargs):
    obj = kwargs['instance']
    p2g = _instantiate_pg2geoserver()
    try:
        p2g.delete_style(obj.name)
    except (urllib2.HTTPError,urllib2.URLError):
        #if something were wrong go on
        pass

@receiver(pre_save, sender=UserStyle)
def style_update_handler(sender, **kwargs):
    new_style = kwargs['instance']
    if new_style.id:
        try:
            style = UserStyle.objects.get(pk=new_style.id)
        except UserStyle.DoesNotExist:
            return
        p2g = _instantiate_pg2geoserver()
        try:
            p2g.delete_style(style.name)
        except (urllib2.HTTPError,urllib2.URLError):
            #if something were wrong go on
            pass

class UserLayer(models.Model):
    user = models.ForeignKey(User, null=True)
    layer = models.ForeignKey(CatalogLayer, unique=True)
    style = models.ForeignKey(UserStyle, on_delete=models.PROTECT)

    def as_dict(self):
        return {'pk': self.pk,
                'layer_name': self.layer.gs_name,
                'label': self.layer.name,
                'style_label': str(self.style),
                'style_name': self.style.name,
                'schema': self.layer.tableschema,
                'workspace': self.layer.gs_workspace,
                'created_at': str(self.layer.creation_time),
                }

    class Meta:
        app_label = u'api'

class CatalogShape(CatalogLayer):
    class Meta:
        app_label = u'api'
        proxy = True

@receiver(pre_delete, sender=CatalogLayer)
def cataloglayer_delete_handler(sender, **kwargs):
    catalogLayer = kwargs['instance']
    shape_utils._delete_layer_postgis(catalogLayer.tableschema,
                                      catalogLayer.tablename)
    shape_utils._remove_layer_geoserver(catalogLayer)

@receiver(pre_save, sender=CatalogLayer)
def catalogLayer_update_handler(sender, **kwargs):
    new_catalogLayer = kwargs['instance']
    if new_catalogLayer.id:
        try:
            catalogLayer = CatalogLayer.objects.get(pk=new_catalogLayer.id)
        except CatalogLayer.DoesNotExist:
            return
        shape_utils._delete_layer_postgis(catalogLayer.tableschema,
                                          catalogLayer.tablename)
        shape_utils._remove_layer_geoserver(catalogLayer)
