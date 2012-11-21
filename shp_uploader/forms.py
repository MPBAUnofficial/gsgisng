from django import forms
from shp_uploader.models import UserStyle, UserLayer
from django.utils.translation import ugettext_lazy as _
import zipfile

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

class ShapeForm(forms.Form):
    layer_name = forms.CharField(max_length=50, label=_(u"Layer name"))
    epsg_code = forms.IntegerField(label=_(u"EPSG:"))
    style = forms.ModelChoiceField(queryset=UserStyle.objects.all())
    shape_zip = forms.FileField()

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

class UserStyleForm(forms.ModelForm):
    #def __init__(self):
    class Meta:
        model = UserStyle
        exclude = ("user", "name")
