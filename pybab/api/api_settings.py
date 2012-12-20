from django.conf import settings

def get(key, default):
  return getattr(settings, key, default)

SCHEMA_USER_UPLOADS = get('SCHEMA_USER_UPLOADS',
                          'users_uploads').replace(" ","_")
WORKSPACE_USER_UPLOADS = get('WORKSPACE_USER_UPLOADS',
                             'users_uploads').replace(" ","_")
DATASTORE_USER_UPLOADS = get('DATASTORE_USER_UPLOADS',
                             'usersuploads').replace(" ","_")
SCHEMA_ADMIN_UPLOADS = get('SCHEMA_ADMIN_UPLOADS',
                           'admin_uploads').replace(" ","_")
WORKSPACE_ADMIN_UPLOADS = get('WORKSPACE_ADMIN_UPLOADS',
                              'admin_uploads').replace(" ","_")
DATASTORE_ADMIN_UPLOADS = get('DATASTORE_ADMIN_UPLOADS',
                              'adminuploads').replace(" ","_")
GEOSERVER_URL = get('GEOSERVER_URL', 'http://localhost:8080')
GEOSERVER_PUBLIC_PATH = get('GEOSERVER_PUBLIC_PATH', '/geoserver/ows')
GEOSERVER_USER = get('GEOSERVER_USER', 'admin')
GEOSERVER_PASSWORD = get('GEOSERVER_PASSWORD', 'geoserver')
MAX_LAYER_UPLOADS = get('MAX_LAYER_UPLOADS', 100)
MAX_STYLE_UPLOADS = get('MAX_STYLE_UPLOADS', 20)

# 100000
MAX_GROUPS = get('MAX_GROUPS', 10**5)

def alter_id(instance):
    return {'id':instance.id*MAX_GROUPS,
            'real_id':instance.id}