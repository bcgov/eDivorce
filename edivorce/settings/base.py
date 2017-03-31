"""
Django settings for this project.

Generated by 'django-admin startproject' using Django 1.8.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import os
from unipath import Path

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_DIR = Path(__file__).parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# The SECRET_KEY is provided via an environment variable in OpenShift
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    default='9e4@&tw46$l31)zrqe3wi+-slqm(ruvz&se0^%9#6(_w3ui!c0'
)

DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'debug_toolbar',
    'edivorce.apps.core',
    'compressor',
    'crispy_forms'
)

MIDDLEWARE_CLASSES = (
    'edivorce.apps.core.middleware.basicauth_middleware.BasicAuthMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'edivorce.apps.core.middleware.bceid_middleware.BceidMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

ROOT_URLCONF = 'edivorce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['edivorce/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'edivorce.apps.core.context_processors.settings_processor'
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'

# need to disable auth in Django Rest Framework so it doesn't get triggered
# by presence of Basic Auth headers
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': []
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

BCGOV_NETWORK = os.environ.get('PROXY_NETWORK', '0.0.0.0/0')

FORCE_SCRIPT_NAME = '/'

FIXTURE_DIRS = (
    os.path.join(PROJECT_ROOT, 'edivorce', 'fixtures'),
)

# Expire sessions after 20 minutes
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 1200 # (seconds)

BASICAUTH_ENABLED = False

# Google Tag Manager (dev/test instance)
GTM_ID = 'GTM-NJLR7LT'
