from django.conf import settings

GEODOCS_NO_CSRF_PROTECTION = getattr(settings, 'GEODOCS_NO_CSRF_PROTECTION', False)
GEODOCS_SRID = getattr(settings, 'GEODOCS_SRID', None)
