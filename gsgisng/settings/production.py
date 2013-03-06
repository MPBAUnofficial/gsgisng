import os
from django.core.exceptions import ImproperlyConfigured
from .base import *

def get_env_variable(var_name):
    """ Get the environment variable or return exception """
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the %s environment variable" % var_name
        raise ImproperlyConfigured(error_msg)

#
# Production settings for gsgisng
#

DEBUG=False
TEMPLATE_DEBUG=False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

#TODO: put STATICFILE_DIRS here
STATICFILE_DIRS = ()

#TODO: same for TEMPLATE_DIRS
TEMPLATE_DIRS = ()

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

SECRET_KEY = get_env_variable('SECRET_KEY')

INSTALLED_APPS = INSTALLED_APP + (
    'raven.contrib.django_compat'
)

RAVEN_CONFIG = {
    'dsn': '',
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

