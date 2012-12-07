from django import forms
from pybab.api.models import UserStatisticalLink

class UserStatisticalLinkForm(forms.ModelForm):
    class Meta:
        model = UserStatisticalLink

