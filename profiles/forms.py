from registration.forms import RegistrationForm
from django import forms
from django.utils.translation import ugettext_lazy as _
from registration.models import RegistrationProfile
from models import UserProfile, GeographicArea

attrs_dict = { 'class': 'required' }

class MyRegistrationForm(RegistrationForm):
    first_name = forms.RegexField(regex=r'^\w+$',
                                  max_length=50,
                                  widget=forms.TextInput(attrs=attrs_dict),
                                  label=_(u'First name'))
    last_name = forms.RegexField(regex=r'^\w+$',
                                 max_length=50,
                                 widget=forms.TextInput(attrs=attrs_dict),
                                 label=_(u'Last name'))
    fiscal_code = forms.CharField(max_length=16,
                                  widget=forms.TextInput(attrs=attrs_dict),
                                  label=_(u'Fiscal code'))
    telephone = forms.CharField(max_length=20,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_(u'Telephone'))
    area = forms.ModelChoiceField(queryset=GeographicArea.objects.all(),
                                  label=_(u'Geographic Area'))
    personal_data = forms.BooleanField(label=_(u'Consent to the use of personal information'))

    def save(self, profile_callback=None):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User``.

        This is essentially a light wrapper around
        ``RegistrationProfile.objects.create_inactive_user()``,
        feeding it the form data and a profile callback (see the
        documentation on ``create_inactive_user()`` for details) if
        supplied.

        """
        new_user = RegistrationProfile.objects.create_inactive_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email'],
            profile_callback=profile_callback)
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_user.save()

        new_profile = UserProfile(
            user=new_user,
            fiscale_code=self.cleaned_data['codice_fiscale'],
            telephone=self.cleaned_data['telefono'],
            area=self.cleaned_data['area'],
            personal_data=self.cleaned_data['personal_data'],)
        new_profile.save()
        return new_user
