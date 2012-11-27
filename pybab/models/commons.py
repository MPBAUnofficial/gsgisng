from django.contrib.gis.db import models

class GeoTreeError(Exception):
    def __init__(self, message):
        super(GeoTreeError, self).__init__(message)

    @classmethod
    def from_db_error(cls, error):
        # TODO: create new instance of GeoTreeError
        # e.g.: instanciate a new cls() using `error` somehow.
        pass

class GeoTreeModel(models.Model):

    def save(self,force_insert=False, force_update=False):
        try:
            super(GeoTreeModel, self).save(self, force_insert=force_insert, force_update=force_update)
        except DatabaseError as err:
            # TODO: find out where to import DatabaseError
            raise GeoTreeError.from_db_error( err )
    class Meta(object):
        abstract=True
        app_label=u'pybab'

class AdditionalData(object):
    def __init__(self):
        self.attributes = []

    def add(self, name, value):
        setattr(self, name, value)

    def __setattr__(self, name, value):
        if name != "attributes":
            self.attributes.append(name)
        super(AdditionalData, self).__setattr__(name, value)
