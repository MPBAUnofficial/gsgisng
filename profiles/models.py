from django.db import models
from django.contrib.auth.models import User

class GeographicArea(models.Model):
    cod = models.CharField(max_length=20)
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User)

    fiscal_code = models.CharField(max_length=16)
    telephone = models.CharField(max_length=20)
    area = models.ForeignKey(GeographicArea)
    personal_data = models.BooleanField()
