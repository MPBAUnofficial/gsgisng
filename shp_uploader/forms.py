from django import forms
from django.conf import settings
from shp_uploader import shp_uploader_settings
from shp_uploader.models import UserStyle, UserLayer
from pybab.models import CatalogLayer, LayerGroup
from django.utils.translation import ugettext_lazy as _
from shp_uploader.shape_utils import _unzip_save, _upload2pg, _toGeoserver
import zipfile, shutil
import time

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
    def __init__(self, user=None, *args, **kwargs):
        if "instance" not in kwargs:
            kwargs["instance"] = CatalogLayer()
        kwargs["instance"].remotehost = settings.DATABASES['default']['HOST']
        kwargs["instance"].remotedb = settings.DATABASES['default']['NAME']
        kwargs["instance"].remoteport = settings.DATABASES['default']['PORT']
        kwargs["instance"].remoteuser = settings.DATABASES['default']['USER']
        kwargs["instance"].remotepass =settings.DATABASES['default']['PASSWORD']
        kwargs["instance"].tableschema = \
            shp_uploader_settings.SCHEMA_USER_UPLOADS
        kwargs["instance"].gs_workspace = \
            shp_uploader_settings.WORKSPACE_USER_UPLOADS
        kwargs["instance"].gs_url = shp_uploader_settings.GEOSERVER_URL
        kwargs["instance"].geom_column = "wkb_geometry"
        kwargs["instance"].layergroup = LayerGroup.objects.get(pk=0)

        super(ShapeForm, self).__init__(*args, **kwargs)
        self.user = user

    epsg_code = forms.IntegerField(label="EPSG:")
    style = forms.ModelChoiceField(queryset=UserStyle.objects.all())
    shape_zip = forms.FileField()

    def clean(self):
        """Uploads the layer to postgis and indexes it on geoserver in order
        to check if everything is correct
        WARNING: this clean method has side effects, it is done that way
        because it needs to raise execptions"""
        cleaned_data = super(ShapeForm, self).clean()

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
        res = _upload2pg(dir, self.cleaned_data['epsg_code'])
        #delete directory with the shape
        shutil.rmtree(dir)
        if not res==True:
            msg = "Failed to store the layer in postgis."
            msg += "Check the EPSG code {} and if the shape is valid.".format(
                self.cleaned_data['epsg_code'])
            raise forms.ValidationError(msg)
        else:
            #index on geoserver
            res = _toGeoserver(layer_id)
            if not res==True:
                _delete_layer_postgis(shp_uploader_settings.SCHEMA_USER_UPLOADS,
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
        catalogLayer.code_column = "null" #why should I set this?

        if commit:
            catalogLayer.save()
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
        model = CatalogLayer
        fields = ("name",)

class UserStyleForm(forms.ModelForm):
    #def __init__(self):
    class Meta:
        model = UserStyle
        exclude = ("user", "name")
