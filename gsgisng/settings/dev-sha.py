from .development import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'geodb_catlas',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '172.16.168.129',
        'PORT': 5432,
    }
}
