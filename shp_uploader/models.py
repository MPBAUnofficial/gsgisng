from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from pg2geoserver import Pg2Geoserver
from shp_uploader import shp_uploader_settings
from django.utils.translation import ugettext_lazy as _
import time
import urllib2

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
    user = models.ForeignKey(User, null=True)
    name = models.CharField(max_length=200)
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
        """Validates the xml indexing it on the geoserver"""
        geoserver_url = shp_uploader_settings.GEOSERVER_URL
        username = shp_uploader_settings.GEOSERVER_USER
        password = shp_uploader_settings.GEOSERVER_PASSWORD
        p2g = Pg2Geoserver(geoserver_url,username,password)
        #if a style was already indexed on geoserver delete it
        if self.name:
            try:
                p2g.delete_style(self.name)
            except (urllib2.HTTPError,urllib2.URLError):
                #if something were wrong go on
                pass
        self.name = self.label + str(self.user.id) + str(int(time.time()))
        try:
            p2g.create_style(self.name, self.xml)
        except urllib2.HTTPError as e:
            raise ValidationError("Could not validate the style.")
        except urllib2.URLError as e:
            raise ValidationError("Could not validate the style: "+str(e))

class UserLayer(models.Model):
    user = models.ForeignKey(User)
    layer_name = models.CharField(max_length=200)
    style = models.ForeignKey(UserStyle)
    label = models.CharField(max_length=200)
    schema = models.CharField(max_length=200)
    workspace = models.CharField(max_length=200)
    datastore = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add = True)

    def as_dict(self):
        return {'pk': self.pk,
                'layer_name': self.layer_name,
                'label': self.label,
                'style_label': str(self.style),
                'style_name': self.style.name,
                'schema': self.schema,
                'workspace': self.workspace,
                'datastore': self.datastore,
                'created_at': str(self.created_at),
                }
