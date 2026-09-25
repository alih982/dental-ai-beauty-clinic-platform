"""
Django settings for Smart Health Platform - Base Configuration

This is the base settings module that contains common settings for all environments.
All configurations are dynamically loaded from environment variables via dynamic_settings.
"""

import os
from pathlib import Path
from datetime import timedelta

# Import dynamic settings
from config.dynamic_settings import settings as dyn_settings

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ===================
# SECURITY SETTINGS
# ===================
SECRET_KEY = dyn_settings.SECRET_KEY
DEBUG = dyn_settings.DEBUG
ALLOWED_HOSTS = dyn_settings.allowed_hosts_list

# ===================
# APPLICATION DEFINITION
# ===================
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'channels',
    'corsheaders',
    'drf_spectacular',  # API documentation
    'django_filters',  # Filtering support
    'django_celery_beat',  # Celery Beat for scheduled tasks
    
    # Core utilities
    'apps.core',
    
    # Local apps
    'apps.appointments',
    'apps.doctors',
    'apps.patients',
    
    # AI Orchestrator
    'apps.ai_orchestrator',
    
    # Core Domain Apps
    'apps.prescriptions',

    # Feature apps
    'apps.accounts',
    'apps.dashboard',
    'apps.chat',
    'apps.pharmacy',
    'apps.cms',
    'apps.reports',
    'apps.notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    
    # Custom middleware
    'apps.core.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ===================
# DATABASE - PostgreSQL
# ===================
DATABASES = {
    'default': dyn_settings.get_database_config()
}

# ===================
# PASSWORD VALIDATION
# ===================
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

# ===================
# INTERNATIONALIZATION
# ===================
LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('fa', 'Persian'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ===================
# STATIC & MEDIA FILES
# ===================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===================
# DJANGO REST FRAMEWORK
# ===================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': dyn_settings.PAGE_SIZE,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    # Throttling disabled - requires Redis
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}

# ===================
# API DOCUMENTATION
# ===================
SPECTACULAR_SETTINGS = {
    'TITLE': dyn_settings.API_TITLE,
    'DESCRIPTION': dyn_settings.API_DESCRIPTION,
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
}

# ===================
# CHANNELS (WebSocket) - Using Redis
# ===================
CHANNEL_LAYERS = dyn_settings.get_channel_layers_config()

# ===================
# CORS SETTINGS
# ===================
CORS_ALLOWED_ORIGINS = dyn_settings.cors_origins_list
CORS_ALLOW_CREDENTIALS = dyn_settings.CORS_ALLOW_CREDENTIALS
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Authorization', 'Content-Type', 'X-CSRFToken']

# ===================
# LOGGING
# ===================
from config.logging_config import LOGGING

# Admin
ADMINS = [
    (dyn_settings.ADMIN_NAME, dyn_settings.ADMIN_EMAIL) if dyn_settings.ADMIN_EMAIL else ('Admin', 'admin@smarthealth.com'),
]
MANAGERS = ADMINS

# Database query logging
DB_QUERY_LOGGING = dyn_settings.DB_QUERY_LOGGING

# ===================
# CACHE - Redis
# ===================
CACHES = dyn_settings.get_cache_config()

# ===================
# SESSION
# ===================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = dyn_settings.SESSION_COOKIE_AGE
SESSION_COOKIE_SECURE = dyn_settings.SESSION_COOKIE_SECURE
SESSION_COOKIE_HTTPONLY = dyn_settings.SESSION_COOKIE_HTTPONLY
SESSION_COOKIE_SAMESITE = dyn_settings.SESSION_COOKIE_SAMESITE

# ===================
# CUSTOM USER MODEL
# ===================
AUTH_USER_MODEL = 'accounts.User'

# ===================
# AUTH REDIRECTS
# ===================
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ===================
# AI SERVICE
# ===================
AI_SERVICE_URL = dyn_settings.AI_SERVICE_URL

# ===================
# CELERY CONFIGURATION
# ===================
CELERY_BROKER_URL = dyn_settings.CELERY_BROKER_URL
CELERY_RESULT_BACKEND = dyn_settings.CELERY_RESULT_BACKEND
CELERY_TASK_SERIALIZER = dyn_settings.CELERY_TASK_SERIALIZER
CELERY_RESULT_SERIALIZER = dyn_settings.CELERY_RESULT_SERIALIZER
CELERY_ACCEPT_CONTENT = dyn_settings.CELERY_ACCEPT_CONTENT
CELERY_TIMEZONE = dyn_settings.CELERY_TIMEZONE
CELERY_TASK_TRACK_STARTED = dyn_settings.CELERY_TASK_TRACK_STARTED
CELERY_TASK_TIME_LIMIT = dyn_settings.CELERY_TASK_TIME_LIMIT
CELERY_WORKER_PREFETCH_MULTIPLIER = dyn_settings.CELERY_WORKER_PREFETCH_MULTIPLIER
CELERY_TASK_ACKS_LATE = dyn_settings.CELERY_TASK_ACKS_LATE

# ===================
# MLFLOW
# ===================
MLFLOW_TRACKING_URI = dyn_settings.MLFLOW_TRACKING_URI

# ===================
# FILE UPLOADS
# ===================
DATA_UPLOAD_MAX_MEMORY_SIZE = dyn_settings.DATA_UPLOAD_MAX_MEMORY_SIZE
FILE_UPLOAD_MAX_MEMORY_SIZE = dyn_settings.FILE_UPLOAD_MAX_MEMORY_SIZE

# ===================
# SECURITY SETTINGS
# ===================
SECURE_SSL_REDIRECT = dyn_settings.SECURE_SSL_REDIRECT
SECURE_PROXY_SSL_HEADER = dyn_settings.SECURE_PROXY_SSL_HEADER
SECURE_HSTS_SECONDS = dyn_settings.SECURE_HSTS_SECONDS
SECURE_HSTS_INCLUDE_SUBDOMAINS = dyn_settings.SECURE_HSTS_INCLUDE_SUBDOMAINS
SECURE_HSTS_PRELOAD = dyn_settings.SECURE_HSTS_PRELOAD
X_FRAME_OPTIONS = dyn_settings.X_FRAME_OPTIONS
SECURE_CONTENT_TYPE_NOSNIFF = dyn_settings.SECURE_CONTENT_TYPE_NOSNIFF

# ===================
# CSRF SETTINGS
# ===================
CSRF_TRUSTED_ORIGINS = dyn_settings.csrf_origins_list

