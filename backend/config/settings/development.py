"""
Development settings for Smart Health Platform

Development-specific settings that override base configuration.
All settings are dynamically loaded from environment variables.
"""

import os
from .base import *
from config.dynamic_settings import settings as dyn_settings

# Enable debug mode for development
DEBUG = True

# ===================
# DATABASE - PostgreSQL (use maggicaihub.com for local development without Docker)
# ===================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': dyn_settings.DB_NAME,
        'USER': dyn_settings.DB_USER,
        'PASSWORD': dyn_settings.DB_PASSWORD,
        'HOST': dyn_settings.DB_HOST,
        'PORT': dyn_settings.DB_PORT,
        
        # Transaction management
        'ATOMIC_REQUESTS': True,
        
        # Connection pooling
        'CONN_MAX_AGE': dyn_settings.DB_CONN_MAX_AGE,
        
        # PostgreSQL optimizations
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': dyn_settings.DB_SSL_MODE,
        },
    }
}

# ===================
# SECURITY - Disable for local development
# ===================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# ===================
# EMAIL - Console for development
# ===================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ===================
# CHANNELS - Redis for development (use maggicaihub.com, DB 1 for channels)
# ===================
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             'hosts': [os.environ.get('REDIS_URL', 'redis://maggicaihub.com:6379/1')],
#         },
#     },
# }
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
# Force using maggicaihub.com for local development (not Docker)
import socket
if os.environ.get('DOCKER_CONTAINER') != 'true':
    # Ensure we're using maggicaihub.com, not Docker hostnames
    pass  # Already handled by the above config

# ===================
# LOGGING - More verbose in development
# ===================
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['root']['level'] = 'DEBUG'

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',  # Useful dev tools
]

# ===================
# CACHE - Redis for development
# ===================
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': os.environ.get('CACHE_URL', dyn_settings.CACHE_URL),
#         'KEY_PREFIX': dyn_settings.CACHE_KEY_PREFIX,
#         'TIMEOUT': dyn_settings.CACHE_TIMEOUT_DEFAULT,
#     }
# }
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'hospital-dev-cache',
        'TIMEOUT': dyn_settings.CACHE_TIMEOUT_DEFAULT,
    }
}
# ===================
# CELERY - Development configuration
# ===================
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', dyn_settings.CELERY_BROKER_URL)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', dyn_settings.CELERY_RESULT_BACKEND)
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = dyn_settings.CELERY_TIMEZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = dyn_settings.CELERY_TASK_TIME_LIMIT

# ===================
# ALLOWED HOSTS - More permissive for development
# ===================
ALLOWED_HOSTS = ['*']

