"""
Unified Dynamic Configuration System for Smart Health Platform

This module provides a single source of truth for ALL configurations.
All settings can be changed via environment variables - no code changes needed!

Usage:
    from config.dynamic_settings import settings
    
    # Access any configuration
    database_url = settings.DATABASE_URL
    redis_url = settings.REDIS_URL
    celery_broker = settings.CELERY_BROKER_URL
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Unified Configuration with validation and smart defaults.
    All values are read from environment variables.
    """
    
    # ===================
    # DJANGO CORE
    # ===================
    DEBUG: bool = False
    SECRET_KEY: str = Field(default="change-me-in-production")
    DJANGO_SETTINGS_MODULE: str = "config.settings.production"  # Use production settings by default
    ALLOWED_HOSTS: str = "maggicaihub.com,127.0.0.1,0.0.0.0,magicai.runflare.run,magggicai-magicai.runflare.run"
    
    # ===================
    # DATABASE
    # ===================
    DB_NAME: str = "postgreshif_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = Field(default="ppIdIZfPaBTFn5h1v8kx")
    DB_HOST: str = "remote-pishgaman.runflare.com"  # Production DB host
    DB_PORT: int = 32686
    DB_SSL_MODE: str = "require"
    DB_CONN_MAX_AGE: int = 600
    
    # ===================
    # REDIS & CACHE - SEPARATED DATABASES
    # ===================
    # Each service uses a different Redis DB index for better isolation
    # Change any of these in .env to update all references automatically!
    REDIS_URL: str = "redis://maggicaihub.com:6379/0"
    REDIS_DB_CELERY: int = 0  # Celery Broker & Result Backend
    REDIS_DB_CHANNELS: int = 1  # Django Channels (WebSocket)
    REDIS_DB_CACHE: int = 2  # Django Cache
    REDIS_DB_SESSIONS: int = 3  # Session storage
    
    # Legacy support - these will use REDIS_DB_CELERY if not set
    CACHE_URL: str = "redis://maggicaihub.com:6379/2"
    
    # ===================
    # CELERY - Complete Setup
    # ===================
    CELERY_BROKER_URL: str = "redis://maggicaihub.com:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://maggicaihub.com:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Tehran"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 1800
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_ENABLE_UTC: bool = True
    CELERYBEAT_SCHEDULER: str = "django_celery_beat.schedulers:DatabaseScheduler"
    
    # ===================
    # CHANNELS (WebSocket)
    # ===================
    CHANNEL_LAYERS_BACKEND: str = "channels.layers.InMemoryChannelLayer"
    CHANNEL_LAYERS_CONFIG: Dict[str, Any] = Field(default_factory=lambda: {})
    
    # ===================
    # SECURITY & CORS
    # ===================
    CORS_ALLOWED_ORIGINS: str = "http://maggicaihub.com:3000,http://127.0.0.1:3000,http://maggicaihub.com,http://127.0.0.1:3000,http://localhost:3000,http://0.0.0.0:3000,http://magicai.runflare.run,http://magggicai-magicai.runflare.run"
    CSRF_TRUSTED_ORIGINS: str = "http://maggicaihub.com:3000,http://127.0.0.1:3000,http://maggicaihub.com,http://127.0.0.1:3000,http://localhost:3000,http://0.0.0.0:3000,http://magicai.runflare.run,http://magggicai-magicai.runflare.run"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # ===================
    # API CONFIGURATION
    # ===================
    API_VERSION: str = "v1"
    API_TITLE: str = "Smart Health Platform API"
    API_DESCRIPTION: str = "API for Smart Health Platform with AI"

    API_PREFIX: str = "/api/"
    
    # ===================
    # FRONTEND URL - Dynamic redirect target
    # ===================
    FRONTEND_URL: str = "http://maggicaihub.com"  # Override with env for Runflare/prod

    
    # ===================
    # AI SERVICE
    # ===================
    AI_PROVIDER: str = "mock"  # gateway, local, mock - Using mock for fast response
    OLLAMA_HOST: str = "http://maggicaihub.com:11434"
    OPENAI_API_KEY: Optional[str] = None
    GEMMA_API_KEY: Optional[str] = None
    AI_SERVICE_URL: str = "http://maggicaihub.com:8001"
    AI_MODEL_NAME: str = "gemma"
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.7
    
    # ===================
    # MLFLOW
    # ===================
    MLFLOW_TRACKING_URI: str = "http://maggicaihub.com:5000"
    MLFLOW_EXPERIMENT_NAME: str = "hospital_app"
    
    # ===================
    # EMAIL (SMTP)
    # ===================
    EMAIL_BACKEND: str = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_HOST_USER: Optional[str] = None
    EMAIL_HOST_PASSWORD: Optional[str] = None
    EMAIL_USE_TLS: bool = True
    EMAIL_TIMEOUT: int = 30
    DEFAULT_FROM_EMAIL: str = "noreply@smarthealth.com"
    
    # ===================
    # ADMIN
    # ===================
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_NAME: str = "Admin"
    
    # ===================
    # LOGGING
    # ===================
    LOG_LEVEL: str = "INFO"
    DB_QUERY_LOGGING: bool = False
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # ===================
    # CACHE SETTINGS
    # ===================
    CACHE_KEY_PREFIX: str = "hospital"
    CACHE_TIMEOUT_DEFAULT: int = 300  # 5 minutes
    CACHE_TIMEOUT_LONG: int = 3600   # 1 hour
    CACHE_TIMEOUT_SHORT: int = 60    # 1 minute
    
    # ===================
    # SESSION
    # ===================
    SESSION_ENGINE: str = "django.contrib.sessions.backends.db"
    SESSION_CACHE_ALIAS: str = "default"
    SESSION_COOKIE_AGE: int = 86400  # 24 hours
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    
    # ===================
    # STATIC & MEDIA
    # ===================
    STATIC_URL: str = "/static/"
    STATIC_ROOT: str = "staticfiles"
    MEDIA_URL: str = "/media/"
    MEDIA_ROOT: str = "media"
    
    # ===================
    # SECURITY
    # ===================
    SECURE_SSL_REDIRECT: bool = False
    SECURE_PROXY_SSL_HEADER: tuple = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS: int = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURE_HSTS_PRELOAD: bool = True
    X_FRAME_OPTIONS: str = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF: bool = True
    
    # ===================
    # RATE LIMITING
    # ===================
    RATE_LIMIT_ANON: str = "100/minute"
    RATE_LIMIT_USER: str = "200/minute"
    RATE_LIMIT_TOKEN: str = "10/minute"
    
    # ===================
    # PAGINATION
    # ===================
    PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # ===================
    # FILE UPLOADS
    # ===================
    DATA_UPLOAD_MAX_MEMORY_SIZE: int = 10485760  # 10MB
    FILE_UPLOAD_MAX_MEMORY_SIZE: int = 10485760  # 10MB
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    
    # ===================
    # WEBSOCKET
    # ===================
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    WEBSOCKET_PING_TIMEOUT: int = 10
    WEBSOCKET_MAX_MESSAGE_SIZE: int = 512000  # 512KB
    
    # ===================
    # VALIDATORS
    # ===================
    
    @field_validator('ALLOWED_HOSTS', 'CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS', mode='before')
    @classmethod
    def split_string(cls, v):
        if isinstance(v, str):
            return v
        return ','.join(v) if v else ''
    
    @field_validator('CELERY_ACCEPT_CONTENT', mode='before')
    @classmethod
    def parse_celery_accept_content(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(',')]
        return v
    
    # ===================
    # COMPUTED PROPERTIES
    # ===================
    
    @property
    def is_production(self) -> bool:
        return not self.DEBUG
    
    @property
    def is_development(self) -> bool:
        return self.DEBUG
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(',') if h.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(',') if o.strip()]
    
    @property
    def csrf_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CSRF_TRUSTED_ORIGINS.split(',') if o.strip()]
    
    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent
    
    @property
    def static_root(self) -> Path:
        return self.base_dir / self.STATIC_ROOT
    
    @property
    def media_root(self) -> Path:
        return self.base_dir / self.MEDIA_ROOT
    
    # ===================
    # REDIS COMPUTED URLS - Dynamic based on DB indices
    # ===================
    
    @property
    def redis_base_url(self) -> str:
        """Get base Redis URL without DB index"""
        # Extract host:port from REDIS_URL
        import re
        match = re.match(r'(redis://[^/]+)', self.REDIS_URL)
        return match.group(1) if match else self.REDIS_URL
    
    @property
    def celery_broker_url(self) -> str:
        """Celery broker URL with dynamic DB"""
        return f"{self.redis_base_url}/{self.REDIS_DB_CELERY}"
    
    @property
    def celery_result_backend_url(self) -> str:
        """Celery result backend URL with dynamic DB"""
        return f"{self.redis_base_url}/{self.REDIS_DB_CELERY}"
    
    @property
    def channels_url(self) -> str:
        """Django Channels URL with dynamic DB"""
        return f"{self.redis_base_url}/{self.REDIS_DB_CHANNELS}"
    
    @property
    def cache_url(self) -> str:
        """Cache URL with dynamic DB (legacy support)"""
        return f"{self.redis_base_url}/{self.REDIS_DB_CACHE}"
    
    @property
    def sessions_url(self) -> str:
        """Session URL with dynamic DB"""
        return f"{self.redis_base_url}/{self.REDIS_DB_SESSIONS}"
    
    # ===================
    # DJANGO DATABASE CONFIG
    # ===================
    
    def get_database_config(self) -> Dict[str, Any]:
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': self.DB_NAME,
            'USER': self.DB_USER,
            'PASSWORD': self.DB_PASSWORD,
            'HOST': self.DB_HOST,
            'PORT': self.DB_PORT,
            'OPTIONS': {
                'connect_timeout': 10,
                'sslmode': self.DB_SSL_MODE,
            },
            'CONN_MAX_AGE': self.DB_CONN_MAX_AGE,
        }
    
    # ===================
    # CACHE CONFIG
    # ===================
    
    def get_cache_config(self) -> Dict[str, Any]:
        return {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'hospital-cache',
                'TIMEOUT': self.CACHE_TIMEOUT_DEFAULT,
            }
        }
    
    # ===================
    # CHANNELS CONFIG
    # ===================
    
    def get_channel_layers_config(self) -> Dict[str, Any]:
        return {
            "default": {
                "BACKEND": self.CHANNEL_LAYERS_BACKEND,
                "CONFIG": {
                    "hosts": [self.channels_url],
                },
            }
        }
    
    # ===================
    # CELERY CONFIG
    # ===================
    
    def get_celery_config(self) -> Dict[str, Any]:
        return {
            'broker_url': self.celery_broker_url,
            'result_backend': self.celery_result_backend_url,
            'task_serializer': self.CELERY_TASK_SERIALIZER,
            'result_serializer': self.CELERY_RESULT_SERIALIZER,
            'accept_content': self.CELERY_ACCEPT_CONTENT,
            'timezone': self.CELERY_TIMEZONE,
            'enable_utc': self.CELERY_ENABLE_UTC,
            'task_track_started': self.CELERY_TASK_TRACK_STARTED,
            'task_time_limit': self.CELERY_TASK_TIME_LIMIT,
            'worker_prefetch_multiplier': self.CELERY_WORKER_PREFETCH_MULTIPLIER,
            'worker_max_tasks_per_child': self.CELERY_WORKER_MAX_TASKS_PER_CHILD,
            'task_acks_late': self.CELERY_TASK_ACKS_LATE,
            'beat_scheduler': self.CELERYBEAT_SCHEDULER,
        }
    
    # ===================
    # CORS CONFIG
    # ===================
    
    def get_cors_config(self) -> Dict[str, Any]:
        return {
            'CORS_ALLOWED_ORIGINS': self.cors_origins_list,
            'CORS_ALLOW_CREDENTIALS': self.CORS_ALLOW_CREDENTIALS,
            'CORS_ALLOW_METHODS': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'CORS_ALLOW_HEADERS': ['Authorization', 'Content-Type', 'X-CSRFToken'],
        }
    
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True,
    )


# ===================
# GLOBAL INSTANCE
# ===================

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance - singleton pattern"""
    return Settings()


# Default instance - use this throughout the app
settings = get_settings()


# ===================
# CONVENIENCE EXPORTS
# ===================

# Database
DATABASE_CONFIG = settings.get_database_config()
DATABASE_URL = settings.database_url

# Cache
CACHE_CONFIG = settings.get_cache_config()
CACHE_URL = settings.CACHE_URL

# Channels
CHANNEL_LAYERS_CONFIG = settings.get_channel_layers_config()

# Celery
CELERY_CONFIG = settings.get_celery_config()
CELERY_BROKER_URL = settings.CELERY_BROKER_URL
CELERY_RESULT_BACKEND = settings.CELERY_RESULT_BACKEND

# Security
ALLOWED_HOSTS = settings.allowed_hosts_list
CORS_ORIGINS = settings.cors_origins_list

# Debug
DEBUG = settings.DEBUG
IS_PRODUCTION = settings.is_production

