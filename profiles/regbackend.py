from registration.backends.default import DefaultBackend
from registration import signals
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site
from registration.models import RegistrationProfile
from django.contrib.auth.models import User
from profiles.models import UserProfile

class RegBackend(DefaultBackend):

    def register(self, request, **kwargs):
        username, email, password = kwargs['username'], kwargs['email'], kwargs['password1']
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)
        new_user = RegistrationProfile.objects.create_inactive_user(username, email,
                                                                    password, site)
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)

        user = User.objects.get(username=new_user.username)
        user.first_name = kwargs['first_name']
        user.last_name = kwargs['last_name']
        user.save()
        new_profile = UserProfile(user=user)
        new_profile.fiscal_code = kwargs['fiscal_code']
        new_profile.telephone = kwargs['telephone']
        new_profile.area = kwargs['area']
        new_profile.personal_data = kwargs['personal_data']
        new_profile.save()

        return new_user
