from django.db.models.signals import post_syncdb
import shp_uploader.models
from shp_uploader import shp_uploader_settings
from django.db import connection, transaction
import django.db.utils

def my_callback(sender, **kwargs):
    cursor = connection.cursor()
    print "Setting up shp_uploader ..."
    schema = shp_uploader_settings.SCHEMA_USER_UPLOADS
    query = "CREATE SCHEMA {};".format(schema)
    with transaction.commit_on_success():
        try:
            cursor.execute(query)
        except django.db.utils.DatabaseError, e:
            #if the schema already exist do nothing
            if ("already exists" not in e.message):
                raise
    query = "CREATE EXTENSION IF NOT EXISTS postgis;"# WITH SCHEMA "+schema
    with transaction.commit_on_success():
        cursor.execute(query)

post_syncdb.connect(my_callback, sender=shp_uploader.models)

