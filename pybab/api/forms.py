from django import forms
from django.conf import settings
from pybab.api.layer_lib.pg2geoserver import Pg2Geoserver
from pybab.api import layer_settings
from pybab.api.models import UserStyle, UserLayer, CatalogShape
from pybab.models import LayerGroup
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from pybab.api.layer_lib.shape_utils import _unzip_save, _upload2pg, \
                                     _toGeoserver, _delete_layer_postgis
import zipfile, shutil
import time
import urllib2

def _instantiate_pg2geoserver():
    geoserver_url = layer_settings.GEOSERVER_URL
    username = layer_settings.GEOSERVER_USER
    password = layer_settings.GEOSERVER_PASSWORD
    return Pg2Geoserver(geoserver_url,username,password)

class UserStyleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserStyleForm, self).__init__(*args, **kwargs)

    def clean(self):
        """Validates the xml indexing it on the geoserver
        Maybe it should be refactorized cause it has side effects
        on the geoserver... This implementation tries to avoid
        side effects problems.
        """
        cleaned_data = super(UserStyleForm, self).clean()
        if self._errors:
            return cleaned_data
        p2g = _instantiate_pg2geoserver()

        label = cleaned_data["label"]
        if self.user:
            self.name = label + str(self.user.id) + str(int(time.time()))
        else:
            self.name = label + "_adm_" + str(int(time.time()))
        try:
            p2g.create_style(self.name, cleaned_data["xml"])
        except urllib2.HTTPError as e:
            raise ValidationError("Could not validate the style.")
        except urllib2.URLError as e:
            raise ValidationError("Could not validate the style: "+str(e))

        return cleaned_data

    def save(self, force_insert=False, force_update=False, commit=True):
        userStyle = super(UserStyleForm, self).save(commit=False)

        userStyle.name = self.name
        userStyle.user = self.user

        if commit:
            userStyle.save()
        return userStyle

    class Meta:
        model = UserStyle
        exclude = ("user", "name")

def _check_number_files(extension, zip):
    """Check that in the zip there is exactly one file with the
    given extension"""
    members = [member for member in zip.namelist()
               if member.lower().endswith(extension)]
    if len(members) != 1:
        msg = _(u"There must be exactly one file with the extension '")
        msg += extension+"'. "+str(len(members))+" given."
        msg.format(extension, str(len(members)))
        raise forms.ValidationError(msg)

class ShapeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if "instance" not in kwargs:
            kwargs["instance"] = CatalogShape()
        self.user = kwargs.pop('user', None)
        kwargs["instance"].remotehost = settings.DATABASES['default']['HOST']
        kwargs["instance"].remotedb = settings.DATABASES['default']['NAME']
        kwargs["instance"].remoteport = settings.DATABASES['default']['PORT']
        kwargs["instance"].remoteuser = settings.DATABASES['default']['USER']
        kwargs["instance"].remotepass =settings.DATABASES['default']['PASSWORD']
        if self.user:
            kwargs["instance"].tableschema = \
                layer_settings.SCHEMA_USER_UPLOADS
            kwargs["instance"].gs_workspace = \
                layer_settings.WORKSPACE_USER_UPLOADS
        else:
            kwargs["instance"].tableschema = \
                layer_settings.SCHEMA_ADMIN_UPLOADS
            kwargs["instance"].gs_workspace = \
                layer_settings.WORKSPACE_ADMIN_UPLOADS
        kwargs["instance"].gs_url = layer_settings.GEOSERVER_URL
        kwargs["instance"].geom_column = "wkb_geometry"
        kwargs["instance"].layergroup = LayerGroup.objects.get(pk=0)

        super(ShapeForm, self).__init__(*args, **kwargs)


    epsg_code = forms.IntegerField(label="EPSG:")
    style = forms.ModelChoiceField(queryset=UserStyle.objects.all())
    shape_zip = forms.FileField()

    def clean(self):
        """Uploads the layer to postgis and indexes it on geoserver in order
        to check if everything is correct
        WARNING: this clean method has side effects, it is done that way
        because it needs to raise execptions"""
        cleaned_data = super(ShapeForm, self).clean()
        if self._errors:
            return cleaned_data

        layer_label = self.cleaned_data["name"]
        if self.user:
            layer_id = layer_label + str(self.user.id) + str(int(time.time()))
        else:
            layer_id = layer_label + "_adm_" + str(int(time.time()))
        self.layer_id = layer_id

        #unzip the file
        dir = _unzip_save(self.cleaned_data["shape_zip"],
                          #request.FILES['shape_zip'],
                          layer_id)
        #store the shape in postgis
        if self.user:
            res = _upload2pg(dir,
                             layer_settings.SCHEMA_USER_UPLOADS,
                             self.cleaned_data['epsg_code'])
        else:
            res = _upload2pg(dir,
                             layer_settings.SCHEMA_ADMIN_UPLOADS,
                             self.cleaned_data['epsg_code'])
        #delete directory with the shape
        shutil.rmtree(dir)
        if not res==True:
            msg = "Failed to store the layer in postgis."
            msg += "Check the EPSG code {} and if the shape is valid.".format(
                self.cleaned_data['epsg_code'])
            raise forms.ValidationError(msg)
        else:
            #index on geoserver
            if self.user:
                res = _toGeoserver(layer_id,False)
            else:
                res = _toGeoserver(layer_id,True)
            if not res==True:
                if self.user:
                    _delete_layer_postgis(layer_settings.SCHEMA_USER_UPLOADS,
                                          layer_id)
                else:
                    _delete_layer_postgis(layer_settings.SCHEMA_ADMIN_UPLOADS,
                                          layer_id)
                msg = "Failed to index the layer on geoserver."
                msg += "The reason was: "+str(res)
                raise forms.ValidationError(msg)

        return cleaned_data

    def save(self, force_insert=False, force_update=False, commit=True):
        catalogLayer = super(ShapeForm, self).save(commit=False)

        catalogLayer.tablename = self.layer_id
        catalogLayer.gs_name = self.layer_id
        catalogLayer.layer_group = LayerGroup.objects.get(pk=0)

        #shuold be if commit. It is forced to commit in order to create
        #the userLayer that is related to it
        if True:
            catalogLayer.save()
            try:
                userLayer = UserLayer.objects.get(layer=catalogLayer)
            except UserLayer.DoesNotExist:
                userLayer = UserLayer()
            userLayer.layer = catalogLayer
            userLayer.style = self.cleaned_data["style"]
            userLayer.user = self.user
            userLayer.save()

        return catalogLayer

    def clean_shape_zip(self):
        zip_file = self.cleaned_data['shape_zip']
        #check if zipfile is correct
        try:
            zip = zipfile.ZipFile(zip_file)
        except zipfile.BadZipfile:
            msg = u"The shape must be compressed in a valid zip file"
            raise forms.ValidationError(_(msg))
        #check if there are files corrupted
        bad_files = zip.testzip()
        zip.close()
        if bad_files:
            msg = u"The shape must be compressed in a valid zip file"
            raise forms.ValidationError(_(msg))
        #check that only one .shp is present
        _check_number_files(".shp",zip)
        #check that only one .dbg is present
        _check_number_files(".dbf",zip)
        #check that only one .prj is present
        _check_number_files(".prj",zip)
        #check that only one .shx is present
        _check_number_files(".shx",zip)
        return zip_file

    class Meta:
        model = CatalogShape
        fields = ("name",)
