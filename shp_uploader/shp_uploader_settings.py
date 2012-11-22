from django.conf import settings

def get(key, default):
  return getattr({}, key, default)

SCHEMA_USER_UPLOADS = get('SCHEMA_USER_UPLOADS',
                          'users_uploads').replace(" ","_")
WORKSPACE_USER_UPLOADS = get('WORKSPACE_USER_UPLOADS',
                             'users_uploads').replace(" ","_")
DATASTORE_USER_UPLOADS = get('DATASTORE_USER_UPLOADS',
                             'users_uploads').replace(" ","_")
GEOSERVER_URL = get('GEOSERVER_URL', 'http://localhost:8080')
GEOSERVER_USER = get('GEOSERVER_USER', 'admin')
GEOSERVER_PASSWORD = get('GEOSERVER_PASSWORD', 'geoserver')
MAX_LAYER_UPLOADS = get('MAX_LAYER_UPLOADS', 100)
MAX_STYLE_UPLOADS = get('MAX_STYLE_UPLOADS', 20)
