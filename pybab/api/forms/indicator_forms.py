from django import forms
from pybab.api.models import UserIndicatorLink

class UserIndicatorLinkForm(forms.ModelForm):
    class Meta:
        model = UserIndicatorLink

