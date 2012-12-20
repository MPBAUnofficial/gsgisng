from django.db.models.signals import post_syncdb
import pybab.api.models
from pybab.api import api_settings
from django.db import connection, transaction
import django.db.utils

def my_callback(sender, **kwargs):
    cursor = connection.cursor()
    print "Setting up pybab.api ..."
    for schema in (api_settings.SCHEMA_USER_UPLOADS,
                   api_settings.SCHEMA_ADMIN_UPLOADS):
        query = "CREATE SCHEMA {0};".format(schema)
        with transaction.commit_on_success():
            try:
                cursor.execute(query)
            except django.db.utils.DatabaseError, e:
                #if the schema already exist do nothing
                if "already exists" not in e.message:
                    raise

post_syncdb.connect(my_callback, sender=pybab.api.models)

