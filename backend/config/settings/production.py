"""
Production settings for Smart Health Platform

Production overrides - security hardened, optimized for server.
"""

from .base import *
from config.dynamic_settings import settings as dyn_settings

# Security hardened for production
DEBUG = False
SECRET_KEY = dyn_settings.SECRET_KEY

# Database - Production PostgreSQL
DATABASES = {
    'default': dyn_settings.get_database_config()
}

# Production Redis/Cache/Channels (use dynamic REDIS_DB_*)
CACHES = dyn_settings.get_cache_config()

CHANNEL_LAYERS = dyn_settings.get_channel_layers_config()

# Celery Production
CELERY_BROKER_URL = dyn_settings.celery_broker_url
CELERY_RESULT_BACKEND = dyn_settings.celery_result_backend_url
CELERY_TASK_SERIALIZER = dyn_settings.CELERY_TASK_SERIALIZER
CELERY_RESULT_SERIALIZER = dyn_settings.CELERY_RESULT_SERIALIZER
CELERY_ACCEPT_CONTENT = dyn_settings.CELERY_ACCEPT_CONTENT
CELERY_TIMEZONE = dyn_settings.CELERY_TIMEZONE
CELERY_TASK_TRACK_STARTED = dyn_settings.CELERY_TASK_TRACK_STARTED
CELERY_TASK_TIME_LIMIT = dyn_settings.CELERY_TASK_TIME_LIMIT
CELERY_WORKER_PREFETCH_MULTIPLIER = dyn_settings.CELERY_WORKER_PREFETCH_MULTIPLIER
CELERY_TASK_ACKS_LATE = dyn_settings.CELERY_TASK_ACKS_LATE

# Production Security
ALLOWED_HOSTS = dyn_settings.allowed_hosts_list
CORS_ALLOWED_ORIGINS = dyn_settings.cors_origins_list
CORS_ALLOW_CREDENTIALS = dyn_settings.CORS_ALLOW_CREDENTIALS
CSRF_TRUSTED_ORIGINS = dyn_settings.csrf_origins_list

SECURE_SSL_REDIRECT = dyn_settings.SECURE_SSL_REDIRECT
SECURE_PROXY_SSL_HEADER = dyn_settings.SECURE_PROXY_SSL_HEADER
SECURE_HSTS_SECONDS = dyn_settings.SECURE_HSTS_SECONDS
SECURE_HSTS_INCLUDE_SUBDOMAINS = dyn_settings.SECURE_HSTS_INCLUDE_SUBDOMAINS
SECURE_HSTS_PRELOAD = dyn_settings.SECURE_HSTS_PRELOAD
X_FRAME_OPTIONS = dyn_settings.X_FRAME_OPTIONS
SECURE_CONTENT_TYPE_NOSNIFF = dyn_settings.SECURE_CONTENT_TYPE_NOSNIFF
SESSION_COOKIE_SECURE = dyn_settings.SESSION_COOKIE_SECURE
SESSION_COOKIE_HTTPONLY = dyn_settings.SESSION_COOKIE_HTTPONLY
SESSION_COOKIE_SAMESITE = dyn_settings.SESSION_COOKIE_SAMESITE

# Production logging (less verbose)
LOGGING['loggers']['apps']['level'] = 'INFO'
LOGGING['root']['level'] = 'WARNING'

# Gunicorn/Production WSGI/ASGI
# Use Daphne for ASGI (Channels/WebSocket)

# Static files - collectstatic required
STATIC_ROOT = dyn_settings.static_root
MEDIA_ROOT = dyn_settings.media_root

# Disable debug toolbar
INSTALLED_APPS = [app for app in INSTALLED_APPS if 'debug_toolbar' not in app]

# Production email (real SMTP)
# EMAIL_BACKEND stays as configured in dynamic_settings

