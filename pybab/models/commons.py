from django.db import connection, transaction, DatabaseError
from django.contrib.gis.db import models

# ===========================================================================
# Raw cursor related stuff
# ===========================================================================

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

def pg_execute(proc_name, args, fetchone=False):
    with get_raw_cursor() as cursor:
        if not fetchone:
            result = pg_run(cursor, proc_name, args).fetchall()
        else:
            result = pg_run(cursor, proc_name, args).fetchone()
    return result

def pg_run(cursor, proc_name, args=None):
    """
    Basically a thin wrapper around `cursor.callproc`
    It returns the cursor itself to allow chained calls.
    e.g.: pg_run(cursor, u'gt_elements_by_label', args).fetchall()
    """
    if args is None:
        args = []
    cursor.callproc(proc_name, args)
    return cursor

# ===========================================================================
# GeoTree common utils
# ===========================================================================

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

    def save(self, *args, **kwargs):
        try:
            super(GeoTreeModel, self).save(*args, **kwargs)
        except DatabaseError as dberr:
            raise GeoTreeError.from_database_error(dberr)

    def delete(self):
        try:
            super(GeoTreeModel, self).delete()
        except DatabaseError as dberr:
            raise GeoTreeError.from_database_error(dberr)

    class Meta(object):
        abstract=True
        managed=False
        app_label=u'pybab'

# ===========================================================================
# Additional data class
# ===========================================================================

class AdditionalData(object):
    def __init__(self):
        self.attributes = []

    def add(self, name, value):
        setattr(self, name, value)

    def __setattr__(self, name, value):
        if name != "attributes":
            self.attributes.append(name)
        super(AdditionalData, self).__setattr__(name, value)
    
    def _add_from_model(self, model, mapping):
        """
        Adds all the fields specified for the model
        into this AdditionalData object.
        A mapping is a dictionary containing the name
        of the attribute on the object and the name of
        the attribute to be added on this instance.
        """
        for obj_attr, data_attr in mapping.items():
            self.add(data_attr, getattr(model, data_attr, None))

    @classmethod
    def attach_to_objects_from_model(cls, queryset, mapping, related_object_name):
        """
        This method takes a queryset, a mapping dictionary and a
        related object name.
        It then iterates through the queryset.
        For each item in the queryset it selects the related object
        specified and initialize a AdditionalData instance on it.
        It then copies all the attributes defined in the mapping
        on the additional_data instance.
        Finally it returns a list of modified related objects.
        """
        result = []
        for model in queryset:
            related_object = getattr(model, related_object_name)
            setattr(related_object, 'additional_data', cls())
            related_object.additional_data._add_from_model(model, mapping)
            result.append(related_object)
        return result
