from django.db import models
from pybab.models import CatalogLayer
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from pg2geoserver import Pg2Geoserver
from shp_uploader import shp_uploader_settings
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from shp_uploader import shape_utils
import time
import urllib2

def _instantiate_pg2geoserver():
    geoserver_url = shp_uploader_settings.GEOSERVER_URL
    username = shp_uploader_settings.GEOSERVER_USER
    password = shp_uploader_settings.GEOSERVER_PASSWORD
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

    def clean(self):
        """Validates the xml indexing it on the geoserver
        Maybe it should be refactorized cause it has side effects
        on the geoserver... This implementation tries to avoid
        side effects problems.
        """
        try:
            self.clean_fields(exclude=('name',))
        except ValidationError, e:
            return
        p2g = _instantiate_pg2geoserver()

        to_delete = None
        #if a style was already indexed on geoserver mark it for deletion
        if self.name:
            to_delete = self.name

        if self.user:
            self.name = self.label + str(self.user.id) + str(int(time.time()))
        else:
            self.name = self.label + "_adm_" + str(int(time.time()))
        try:
            p2g.create_style(self.name, self.xml)
        except urllib2.HTTPError as e:
            raise ValidationError("Could not validate the style.")
        except urllib2.URLError as e:
            raise ValidationError("Could not validate the style: "+str(e))

        #delete previous style
        if to_delete:
            try:
                p2g.delete_style(to_delete)
            except (urllib2.HTTPError,urllib2.URLError):
                #if something were wrong go on
                pass

@receiver(pre_delete, sender=UserStyle)
def style_delete_handler(sender, **kwargs):
    obj = kwargs['instance']
    p2g = _instantiate_pg2geoserver()
    try:
        p2g.delete_style(obj.name)
    except (urllib2.HTTPError,urllib2.URLError):
        #if something were wrong go on
        pass

class UserLayer(models.Model):
    user = models.ForeignKey(User)
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

@receiver(pre_delete, sender=CatalogLayer)
def cataloglayer_delete_handler(sender, **kwargs):
    catalogLayer = kwargs['instance']
    shape_utils._delete_layer_postgis(catalogLayer.tableschema,
                                      catalogLayer.tablename)
    shape_utils._remove_layer_geoserver(catalogLayer)
