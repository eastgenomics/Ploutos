"""
Django settings for Ploutos project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
import json
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read in credentials file in same directory

datafile = BASE_DIR  / "Ploutos" / "CREDENTIALS.json"
with open(datafile, 'r') as credentials_file:
    CREDENTIALS = json.load(credentials_file)

# Assign keys to data from the file
DB_USERNAME = CREDENTIALS.get('DB_USERNAME')
DB_PASSWORD = CREDENTIALS.get('DB_PASSWORD')
SECRET_KEY = CREDENTIALS.get("SECRET_KEY")
DX_TOKEN = CREDENTIALS.get('DNANEXUS_TOKEN')
ORG = CREDENTIALS.get('ORG')
LIVE_STORAGE_COST_MONTH = CREDENTIALS.get('LIVE_STORAGE_COST_MONTH')
ARCHIVED_STORAGE_COST_MONTH = CREDENTIALS.get('ARCHIVED_STORAGE_COST_MONTH')
PROJ_COLOUR_DICT = CREDENTIALS.get('PROJ_COLOUR_DICT', {})
ASSAY_COLOUR_DICT = CREDENTIALS.get('ASSAY_COLOUR_DICT', {})

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'dashboard.apps.DashboardConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'django_extensions',
    'bootstrap4',
    'crispy_forms',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'Ploutos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [f'{BASE_DIR}/dashboard/templates/dashboard/', BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Ploutos.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Ploutos',
        'USER': DB_USERNAME,
        'PASSWORD': DB_PASSWORD,
        'HOST': 'localhost',
        'PORT': '3306',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'GMT'

USE_I18N = True

USE_TZ = True

# Settings for logging
with open('ploutos-error.log', 'a'):
    pass
with open('ploutos-debug.log', 'a'):
    pass
# Set up execution tracker log
with open('executions_log.log', 'a'):
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('{levelname} {asctime} {module}'
                        '{process:d} {thread:d} {message}'),
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    # Handlers
    'handlers': {
        'error-log': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'ploutos-error.log',
            'formatter': 'simple',
            'maxBytes': 5242880,
            'backupCount': 2
        },
        'debug-log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'ploutos-debug.log',
            'formatter': 'verbose',
            'maxBytes': 5242880,
            'backupCount': 2
        },
    },
    # Loggers
    'loggers': {
        'general': {
            'handlers': ['error-log'],
            'level': 'ERROR',
            'propagate': True
        },
        '': {
            'handlers': ['debug-log'],
            'level': 'DEBUG',
            'propagate': True
        }
    },
}

# Settings for logging
with open('ploutos-error.log', 'a'):
    pass
with open('ploutos-debug.log', 'a'):
    pass
# Set up execution tracker log
with open('executions_log.log', 'a'):
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    # Handlers
    'handlers': {
        'error-log': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'ploutos-error.log',
            'formatter': 'simple',
            'maxBytes': 5242880,
            'backupCount': 2
        },
        'debug-log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'ploutos-debug.log',
            'formatter': 'verbose',
            'maxBytes': 5242880,
            'backupCount': 2
        },
    },
    # Loggers
    'loggers': {
        'general': {
            'handlers': ['error-log'],
            'level': 'ERROR',
            'propagate': True
        },
        '': {
            'handlers': ['debug-log'],
            'level': 'DEBUG',
            'propagate': True
        }
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, '/')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "dashboard/static/dashboard"),
)

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Log out when the browser is closed
# Also log user out after half an hour of inactivity
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 30 * 60
SESSION_SAVE_EVERY_REQUEST = True