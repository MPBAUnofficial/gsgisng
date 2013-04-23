# -*- coding: utf-8 -*-import os
from unipath import Path

gettext = lambda s:s

PROJECT_DIR = Path(__file__).ancestor(3)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Shamar Droghetti', 'droghetti@fbk.eu'), 
    ('Roberto Bampi', 'robampi@fbk.eu'),
    ('Gabriele Franch', 'franch@fbk.eu'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'gsgisng',                      # Or path to database file if using sqlite3.
        'USER': 'postgres',                      # Not used with sqlite3.
        'PASSWORD': 'postgres',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
    }
}

LANGUAGES = (
    ('en', gettext("english")),
    ('it', gettext("italian")),
)

TIME_ZONE = 'Europe/Rome'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ID = 1

MEDIA_ROOT = ''
MEDIA_URL = '/media/'

STATIC_ROOT = ''
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    PROJECT_DIR.child('gsgisng').child('static'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

TEMPLATE_DIRS = (
    PROJECT_DIR.child('gsgisng').child('templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'cms.context_processors.media',
    'sekizai.context_processors.sekizai',
    'gsgisng.context_processors.home_page_id',
)

FIXTURE_DIRS = (
    PROJECT_DIR.child('gsgisng').child('fixtures'),
)

THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    #'easy_thumbnails.processors.scale_and_crop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'cms.middleware.multilingual.MultilingualURLMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
)

#TODO: investigate multiple wsgi applications for development and production
WSGI_APPLICATION = 'gsgisng.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'south',

    # CMS-related stuff
    'mptt',
    'menus',
    'sekizai',
    'cms',
    'cms.plugins.text',

    'easy_thumbnails',
    'filer',
    'cmsplugin_filer_image',
    'cmsplugin_image_gallery',
    'cmsplugin_newswithimages',

    'registration',

    #TODO: refactor into gswebgis module
    'pg_fuzzysearch',
    'profiles',
    'avatar',
)

# Django cms templates
CMS_TEMPLATES = (
    ('main.html', gettext("One column template")),
    ('two_columns.html', gettext("Two columns template")),
)

#Django registration
ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_REDIRECT_URL="/"


