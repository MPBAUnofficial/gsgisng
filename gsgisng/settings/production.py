from django.core.exceptions import ImproperlyConfigured
from .base import *

def get_settings():
    try:
        with open('production_settings.json', 'r') as f:
            s = json.read(f)
        return s.get
    except KeyError:
        raise ImproperlyConfigured("could not find production_settings.json")

sett = get_settings()

#
# Production settings for gsgisng
#

DEBUG=False
TEMPLATE_DEBUG=False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': sett('db_name'),
        'USER': sett('db_user'),
        'PASSWORD': sett('db_password'),
        'HOST': sett('db_host'),
        'PORT': sett('db_port'),
    }
}

STATIC_ROOT = PROJECT_DIR.ancestor(2).child('static')
MEDIA_ROOT = PROJECT_DIR.ancestor(2).child('media')




MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

SECRET_KEY = sett('secret_key')

INSTALLED_APPS = INSTALLED_APP + (
    'raven.contrib.django_compat'
)

RAVEN_CONFIG = {
    'dsn': sett('sentry_dsn'),
}

# Mail settings
EMAIL_HOST = 'mailhost.fbk.eu'
DEFAULT_FROM_EMAIL = 'registrazione@fbk.eu'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
    },
    'loggers': {
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

