"""
Enhanced Logging Configuration for Django Backend
Includes structured logging, request tracking, and database query logging
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {asctime} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        # Console handler
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        
        # Console handler with colors (development)
        'console_verbose': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        
        # General application log
        'file_app': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        
        # Error log (errors and above)
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'error.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        
        # Database queries log
        'file_db': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'database.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        
        # Security log
        'file_security': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        
        # API requests log
        'file_api': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'api.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        
        # Structured JSON log for production monitoring
        'file_json': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.json.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 20,
            'formatter': 'json',
        },
        
        # Email admins for critical errors
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'root': {
        'handlers': ['console', 'file_app', 'file_error'],
        'level': 'INFO',
    },
    'loggers': {
        # Django framework logs
        'django': {
            'handlers': ['console', 'file_app'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        
        # Django request logs
        'django.request': {
            'handlers': ['file_error', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        
        # Django database queries
        'django.db.backends': {
            'handlers': ['file_db'],
            'level': os.getenv('DB_LOG_LEVEL', 'INFO'),  # Set to DEBUG to log queries
            'propagate': False,
        },
        
        # Security-related logs
        'django.security': {
            'handlers': ['file_security', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Application logs
        'apps': {
            'handlers': ['console_verbose', 'file_app', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        # Appointments app
        'apps.appointments': {
            'handlers': ['console_verbose', 'file_app'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        # API logs
        'api': {
            'handlers': ['file_api', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Base layer logs
        'base': {
            'handlers': ['console_verbose', 'file_app'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        # Channels/WebSocket logs
        'channels': {
            'handlers': ['console', 'file_app'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Celery logs (if using)
        'celery': {
            'handlers': ['console', 'file_app'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # JSON structured logs for monitoring
        'monitoring': {
            'handlers': ['file_json'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# PostgreSQL-specific logging configuration
def get_db_logging_config(enable_query_logging=False):
    """
    Get database-specific logging configuration.
    
    Args:
        enable_query_logging: If True, log all SQL queries (use with caution in production)
    """
    if enable_query_logging:
        LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'
    
    return LOGGING
