from django.db import connection, transaction, DatabaseError
from django.contrib.gis.db import models

class get_raw_cursor(object):
    def __init__(self, cursor_name=None):
        if cursor_name is not None:
            self.cursor_name = cursor_name

    def __enter__(self):
        if getattr(self, 'cursor_name', None) is not None:
            return connection.cursor(self.cursor_name)
        else:
            return connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            transaction.rollback()
            return False # Raise the exception up ...

        transaction.commit_unless_managed()

class GeoTreeError(DatabaseError):
    def __init__(self, message):
        super(GeoTreeError, self).__init__(message)

    @classmethod
    def from_database_error(cls, error):
        # TODO: create new instance of GeoTreeError
        # e.g.: instanciate a new cls() using `error` somehow.
        # For now it just returns the exception itself
        return error

class GeoTreeModel(models.Model):

    def save(self,force_insert=False, force_update=False):
        try:
            super(GeoTreeModel, self).save(force_insert=force_insert, force_update=force_update)
        except DatabaseError as dberr:
            raise GeoTreeError.from_database_error(dberr)

####  ma che caz... e' sto codice???   ###
#    def delete(self):
#        try:
#            super(GeoTreeModel, self).save()
#        except DatabaseError as dberr:
#            raise GeoTreeError.from_database_error(dberr)

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
