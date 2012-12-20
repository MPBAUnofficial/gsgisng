from django.conf import settings
from psycopg2 import DatabaseError
from django.db import connection, transaction
from pybab.api import api_settings
import shutil, tempfile
import zipfile
import urllib2
import os

#internal libraries
import create_ws_ds
from pg2geoserver import Pg2Geoserver
import ogr2ogr

def _unzip_save(zip_file, layer):
    """Unzip the file given to a temporary directory: the path is returned"""
    zip = zipfile.ZipFile(zip_file)
    dir = tempfile.mkdtemp()
    #extract the 4 shape files to dir
    for member in zip.namelist():
        if member.lower().endswith((".shp",".dbf",".prj",".shx")):
            _, extension = os.path.splitext(member)
            path = os.path.join(dir, layer+extension)
            source = zip.open(member)
            target = file(path, "wb")
            shutil.copyfileobj(source, target)
            source.close()
            target.close()
    zip.close()
    return dir

def _upload2pg(dir, schema, epsg_code):
    """Tries to upload the shapefile to postgres. If something went wrong
    it returns the problem, returns True otherwise"""
    db_conf = settings.DATABASES['default']
    #maybe better to use a system with ogr2ogr?
    args = ['ogr2ogr.py',
        '-f', 'PostgreSQL',
        'PG:host={0} user={1} dbname={2} password={3} active_schema={4}\
        '.format(db_conf['HOST'],db_conf['USER'],db_conf['NAME'],
                 db_conf['PASSWORD'],schema),
        '-a_srs', 'EPSG:'+str(epsg_code),
        '-lco', 'PRECISION=NO',
        dir]
    try:
        return ogr2ogr.main(args)
    except Exception, e:
        #the module ogr2ogr doesn't specify witch exception could be
        #raised, try the generic one
        return e.message

def _toGeoserver(layer_name,admin):
    """Tries to index the shapefile in geoserver. If something went wrong
    it returns the problem, returns True otherwise"""
    geoserver_url = api_settings.GEOSERVER_URL
    username = api_settings.GEOSERVER_USER
    password = api_settings.GEOSERVER_PASSWORD
    p2g = Pg2Geoserver(geoserver_url,username,password)
    if admin:
        workspace = api_settings.WORKSPACE_ADMIN_UPLOADS
        datastore = api_settings.DATASTORE_ADMIN_UPLOADS
        schema = api_settings.SCHEMA_ADMIN_UPLOADS
    else:
        workspace = api_settings.WORKSPACE_USER_UPLOADS
        datastore = api_settings.DATASTORE_USER_UPLOADS
        schema = api_settings.SCHEMA_USER_UPLOADS
    try:
        p2g.create_layer(workspace=workspace,
                         datastore=datastore,
                         name=layer_name)
    except urllib2.HTTPError, e:
        #maybe the workspace or the datastore were deleted: tries to create them
        #and index the layer again
        try:
            create_ws_ds.create_ws_ds(workspace,datastore,schema)
        except create_ws_ds.WorkspaceCreationFailed as e:
            return "Failed to create workspace: "+str(e)
        except create_ws_ds.DatastoreCreationFailed as e:
            return "Failed to create datastore: "+str(e)
        else:
            try:
                p2g.create_layer(workspace=workspace,
                                 datastore=datastore,
                                 name=layer_name)
            except urllib2.HTTPError, e:
                return "Failed to index the layer: "+e.read()
    except urllib2.URLError, e:
        return e.reason
    return True

def _delete_layer_postgis(schema,layer_name):
    """Remove layer from postgis"""
    cursor = connection.cursor()
    query = """
CREATE OR REPLACE FUNCTION gt_drop_table(schema_name name, table_name name)
   RETURNS void AS
$BODY$
BEGIN
     EXECUTE 'DROP TABLE '||
quote_ident(schema_name)||'.'||quote_ident(table_name);
END
$BODY$
   LANGUAGE plpgsql;"""
    with transaction.commit_on_success():
        try:
            cursor.execute(query)
            cursor.callproc("gt_drop_table",
                            [schema,layer_name])
        except DatabaseError as e:
            #if the layer could not be elimitade do nothing
            print e
    return

def _remove_layer_geoserver(layer):
    #remove layer from geoserver
    geoserver_url = api_settings.GEOSERVER_URL
    username = api_settings.GEOSERVER_USER
    password = api_settings.GEOSERVER_PASSWORD
    p2g = Pg2Geoserver(geoserver_url,username,password)
    try:
        p2g.delete_layer(layer_name=layer.gs_name)
    except (urllib2.HTTPError, urllib2.URLError), e:
        #if there were problems do nothing:
        #go on with the elminiation of the layer
        print e
