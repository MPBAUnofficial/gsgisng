from shp_uploader import shp_uploader_settings
from django.conf import settings
from pg2geoserver import Pg2Geoserver
import urllib2

class GeoserverUnreachable(urllib2.URLError):
    """The geoserver could not be reached"""
    pass

class WorkspaceCreationFailed(Exception):
    """Failed creating workspace"""
    pass

class DatastoreCreationFailed(Exception):
    """Failed creating datastore"""
    pass

def create_ws_ds():
    """Create the workspace and the datastore needed in the geoserver"""
    geoserver_url = shp_uploader_settings.GEOSERVER_URL
    username = shp_uploader_settings.GEOSERVER_USER
    password = shp_uploader_settings.GEOSERVER_PASSWORD
    p2g = Pg2Geoserver(geoserver_url,username,password)

    workspace = shp_uploader_settings.WORKSPACE_USER_UPLOADS
    datastore = shp_uploader_settings.DATASTORE_USER_UPLOADS
    db_conf = settings.DATABASES['default']
    schema = shp_uploader_settings.SCHEMA_USER_UPLOADS

    try:
        p2g.create_workspace(workspace)
    except urllib2.HTTPError, e:
        raise WorkspaceCreationFailed(e.msg)
    except urllib2.URLError, e:
        raise GeoserverUnreachable(e)

    try:
        p2g.create_datastore(workspace=workspace,
                             name=datastore,
                             pg_host=db_conf['HOST'],
                             pg_port=db_conf['PORT'],
                             database=db_conf['NAME'],
                             schema=schema,
                             user=db_conf['USER'],
                             password=db_conf['PASSWORD'])
    except urllib2.HTTPError, e:
        if not hasattr(e, 'read') or "already exists" not in e.read():
            raise DatastoreCreationFailed(e.msg)
    except urllib2.URLError, e:
        raise GeoserverUnreachable(e)

