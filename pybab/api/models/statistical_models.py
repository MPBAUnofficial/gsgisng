from django.db import models
from django.contrib.auth.models import User

from pybab.models import CatalogStatistical

class UserStatisticalLink(models.Model):
    user = models.ForeignKey(User)
    catalog_statistical = models.ForeignKey(CatalogStatistical, related_name="related_user_set")

    class Meta:
        app_label = u'api'
