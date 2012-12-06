from django.db import models
from django.contrib.auth.models import User
from pybab.models import CatalogIndicator

class UserIndicatorLink(models.Model):
    user = models.ForeignKey(User)
    catalog_statistical = models.ForeignKey(CatalogIndicator, related_name="related_user_set")
    class Meta:
        app_label = u'api'
