"""
Centralized Environment Configuration for Smart Health Platform

All configuration values should be set via environment variables.
This module uses Pydantic for validation and type safety.

Environment Variables:
----------------------
Django Core:
    - DEBUG: Enable debug mode (default: False)
    - SECRET_KEY: Django secret key (required)
    - ALLOWED_HOSTS: Comma-separated list of allowed hosts
    - DJANGO_SETTINGS_MODULE: Settings module (config.settings.production)

Database:
    - DB_NAME: Database name (default: smart_health)
    - DB_USER: Database username (default: health_user)
    - DB_PASSWORD: Database password (required)
    - DB_HOST: Database host (default: maggicaihub.com)
    - DB_PORT: Database port (default: 5432)
    - DB_SSL_MODE: SSL mode for PostgreSQL (default: require)

Redis & Celery:
    - REDIS_URL: Redis connection URL (default: redis://maggicaihub.com:6379/0)
    - CELERY_BROKER_URL: Celery broker URL
    - CELERY_RESULT_BACKEND: Celery result backend

Security:
    - CORS_ALLOWED_ORIGINS: Comma-separated CORS origins
    - CSRF_TRUSTED_ORIGINS: Comma-separated CSRF trusted origins

AI Service:
    - AI_PROVIDER: AI provider (gateway, local, mock)
    - OLLAMA_HOST: Ollama host URL
    - OPENAI_API_KEY: OpenAI API key
    - GEMMA_API_KEY: Google Gemini API key

Email:
    - EMAIL_HOST: SMTP server host
    - EMAIL_PORT: SMTP server port
    - EMAIL_HOST_USER: SMTP username
    - EMAIL_HOST_PASSWORD: SMTP password

External Services:
    - AI_SERVICE_URL: AI service URL
    - MLFLOW_TRACKING_URI: MLflow tracking URI
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List
from pathlib import Path
import os


class AppConfig(BaseSettings):
    """
    Centralized Application Configuration using Pydantic.
    All settings are validated and have sensible defaults.
    """
    
    # ===================
    # Django Core
    # ===================
    DEBUG: bool = False
    SECRET_KEY: str = Field(default="CHANGE-ME-IN-PRODUCTION")
    ALLOWED_HOSTS: str = "maggicaihub.com,127.0.0.1,0.0.0.0"
    DJANGO_SETTINGS_MODULE: str = "config.settings.production"
    
    # ===================
    # Database
    # ===================
    DB_NAME: str = "smart_health"
    DB_USER: str = "health_user"
    DB_PASSWORD: str = Field(default="CHANGE-ME-IN-PRODUCTION")
    DB_HOST: str = "maggicaihub.com"
    DB_PORT: int = 5432
    DB_SSL_MODE: str = "require"
    DB_CONN_MAX_AGE: int = 600
    
    # ===================
    # Redis & Cache
    # ===================
    REDIS_URL: str = "redis://maggicaihub.com:6379/0"
    CACHE_URL: str = "redis://maggicaihub.com:6379/1"
    
    # ===================
    # Celery
    # ===================
    CELERY_BROKER_URL: str = "redis://maggicaihub.com:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://maggicaihub.com:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Tehran"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 1800  # 30 minutes
    
    # ===================
    # Security & CORS
    # ==================================================================================================
    CORS_ALLOWED_ORIGINS: str = "http://maggicaihub.com:3000,http://127.0.0.1:3000,magicai.runflare.run"
    CSRF_TRUSTED_ORIGINS: str = "http://maggicaihub.com:3000,http://127.0.0.1:3000,magicai.runflare.run"
    
    # ===================
    # API Configuration
    # ===================
    API_VERSION: str = "v1"
    API_TITLE: str = "Smart Health Platform API"
    API_DESCRIPTION: str = "API documentation for Smart Health Platform with AI assistant"
    
    # ===================
    # AI Service
    # ===================
    AI_PROVIDER: str = "gateway"  # Options: gateway, local, mock - Using gateway for production
    OLLAMA_HOST: str = "http://maggicaihub.com:11434"
    OPENAI_API_KEY: Optional[str] = None
    GEMMA_API_KEY: Optional[str] = None
    AI_SERVICE_URL: str = "magggicai-magicai.runflare.run"
    
    # ===================
    # MLflow
    # ===================
    MLFLOW_TRACKING_URI: str = "http://maggicaihub.com:5000"
    
    # ===================
    # Email (SMTP)
    # ===================
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_HOST_USER: Optional[str] = None
    EMAIL_HOST_PASSWORD: Optional[str] = None
    EMAIL_USE_TLS: bool = True
    EMAIL_TIMEOUT: int = 30
    
    # ===================
    # Admin
    # ===================
    ADMIN_EMAIL: Optional[str] = None
    
    # ===================
    # Logging
    # ===================
    LOG_LEVEL: str = "INFO"
    DB_QUERY_LOGGING: bool = False
    
    @field_validator('ALLOWED_HOSTS', 'CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS', mode='before')
    @classmethod
    def split_hosts(cls, v: str) -> str:
        """Convert comma-separated string to list for Django"""
        if isinstance(v, str):
            return v
        return ','.join(v)
    
    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get allowed hosts as list"""
        return [h.strip() for h in self.ALLOWED_HOSTS.split(',') if h.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(',') if o.strip()]
    
    @property
    def csrf_origins_list(self) -> List[str]:
        """Get CSRF trusted origins as list"""
        return [o.strip() for o in self.CSRF_TRUSTED_ORIGINS.split(',') if o.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG
    
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / '.env',
        env_file_encoding='utf-8',
        extra='ignore',  # Ignore extra fields in .env
        case_sensitive=True,  # Environment variables are case-sensitive
    )


# Global Config Instance
config = AppConfig()


# Convenience functions
def get_database_config() -> dict:
    """Get Django database configuration dictionary"""
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config.DB_NAME,
        'USER': config.DB_USER,
        'PASSWORD': config.DB_PASSWORD,
        'HOST': config.DB_HOST,
        'PORT': config.DB_PORT,
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': config.DB_SSL_MODE,
        },
        'CONN_MAX_AGE': config.DB_CONN_MAX_AGE,
    }


def get_cache_config() -> dict:
    """Get Django cache configuration dictionary"""
    return {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': config.CACHE_URL,
            'KEY_PREFIX': 'DoctorHub',
            'TIMEOUT': 300,
        }
    }


def get_channel_layers_config() -> dict:
    """Get Django channels configuration dictionary"""
    return {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [config.REDIS_URL],
            },
        }
    }

