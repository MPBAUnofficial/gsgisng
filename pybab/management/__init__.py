from django.db.models.signals import post_syncdb
from django.db import connection, transaction
import pybab
import os

SQL_FILES = ["geotree_core.sql",
             "geotree_api_core.sql",
             "geotree_api_plr.sql",
             "geotree_api_addon.sql"]

def is_geotree():
    tables = (u'gt_attribute',
              u'gt_catalog',
              u'gt_catalog_indicator',
              u'gt_catalog_layer',
              u'gt_cagalog_statistics',
              u'gt_element',
              u'gt_element_catalog',
              u'gt_label',
              u'gt_meta',
              u'gt_tree')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM information_schema.tables "
                   "WHERE table_name IN %s;", [tables])

    return cursor.rowcount==len(tables)

# Dummy callback
def my_callback(sender, **kwargs):
    pass
#TODO: fix this
#def my_callback(sender, **kwargs):
#    if not is_geotree():
#        cursor = connection.cursor()
#        print "Setting up pybab..."
#        for sql_file in SQL_FILES:
#            with open(os.path.join("pybab/management",sql_file),"r") as f:
#                query = f.read()
#                with transaction.commit_on_success():
#                    pass
#-------------- it doesn't work, we need to fix it!
#                    #cursor.execute(query)

post_syncdb.connect(my_callback, sender=pybab.models)
