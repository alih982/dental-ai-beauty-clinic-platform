"""
Fixed version of dynamic_settings.py - Indentation corrected
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    DEBUG: bool = False
    SECRET_KEY: str = Field(default="change-me-in-production")
    DJANGO_SETTINGS_MODULE: str = "config.settings.production"
    ALLOWED_HOSTS: str = "maggicaihub.com,127.0.0.1,0.0.0.0,magicai.runflare.run,magggicai-magicai.runflare.run"
    
    DB_NAME: str = "postgreshif_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = Field(default="ppIdIZfPaBTFn5h1v8kx")
    DB_HOST: str = "remote-pishgaman.runflare.com"
    DB_PORT: int = 32686
    DB_SSL_MODE: str = "require"
    DB_CONN_MAX_AGE: int = 600
    
    REDIS_URL: str = "redis://maggicaihub.com:6379/0"
    REDIS_DB_CELERY: int = 0
    REDIS_DB_CHANNELS: int = 1
    REDIS_DB_CACHE: int = 2
    REDIS_DB_SESSIONS: int = 3
    
    CACHE_URL: str = "redis://maggicaihub.com:6379/2"
    
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
    
    CHANNEL_LAYERS_BACKEND: str = "channels.layers.InMemoryChannelLayer"
    CHANNEL_LAYERS_CONFIG: Dict[str, Any] = Field(default_factory=lambda: {})
    
    CORS_ALLOWED_ORIGINS: str = "http://maggicaihub.com:3000,http://127.0.0.1:3000,http://maggicaihub.com,http://127.0.0.1:3000,http://localhost:3000,http://0.0.0.0:3000,http://magicai.runflare.run,http://magggicai-magicai.runflare.run"
    CSRF_TRUSTED_ORIGINS: str = "http://maggicaihub.com:3000,http://127.0.0.1:3000,http://maggicaihub.com,http://127.0.0.1:3000,http://localhost:3000,http://0.0.0.0:3000,http://magicai.runflare.run,http://magggicai-magicai.runflare.run"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    API_VERSION: str = "v1"
    API_TITLE: str = "Smart Health Platform API"
    API_DESCRIPTION: str = "API for Smart Health Platform with AI"
    API_PREFIX: str = "/api/"
    
    FRONTEND_URL: str = "http://maggicaihub.com"
    
    AI_PROVIDER: str = "mock"
    OLLAMA_HOST: str = "http://maggicaihub.com:11434"
    OPENAI_API_KEY: Optional[str] = None
    GEMMA_API_KEY: Optional[str] = None
    AI_SERVICE_URL: str = "http://maggicaihub.com:8001"
    AI_MODEL_NAME: str = "gemma"
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.7
    
    MLFLOW_TRACKING_URI: str = "http://maggicaihub.com:5000"
    MLFLOW_EXPERIMENT_NAME: str = "hospital_app"
    
    EMAIL_BACKEND: str = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_HOST_USER: Optional[str] = None
    EMAIL_HOST_PASSWORD: Optional[str] = None
    EMAIL_USE_TLS: bool = True
    EMAIL_TIMEOUT: int = 30
    DEFAULT_FROM_EMAIL: str = "noreply@smarthealth.com"
    
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_NAME: str = "Admin"
    
    LOG_LEVEL: str = "INFO"
    DB_QUERY_LOGGING: bool = False
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    CACHE_KEY_PREFIX: str = "hospital"
    CACHE_TIMEOUT_DEFAULT: int = 300
    CACHE_TIMEOUT_LONG: int = 3600
    CACHE_TIMEOUT_SHORT: int = 60
    
    SESSION_ENGINE: str = "django.contrib.sessions.backends.db"
    SESSION_CACHE_ALIAS: str = "default"
    SESSION_COOKIE_AGE: int = 86400
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    
    STATIC_URL: str = "/static/"
    STATIC_ROOT: str = "staticfiles"
    MEDIA_URL: str = "/media/"
    MEDIA_ROOT: str = "media"
    
    SECURE_SSL_REDIRECT: bool = False
    SECURE_PROXY_SSL_HEADER: tuple = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS: int = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURE_HSTS_PRELOAD: bool = True
    X_FRAME_OPTIONS: str = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF: bool = True
    
    RATE_LIMIT_ANON: str = "100/minute"
    RATE_LIMIT_USER: str = "200/minute"
    RATE_LIMIT_TOKEN: str = "10/minute"
    
    PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    DATA_UPLOAD_MAX_MEMORY_SIZE: int = 10485760
    FILE_UPLOAD_MAX_MEMORY_SIZE: int = 10485760
    MAX_UPLOAD_SIZE: int = 10485760
    
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    WEBSOCKET_PING_TIMEOUT: int = 10
    WEBSOCKET_MAX_MESSAGE_SIZE: int = 512000
    
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
    
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True,
    )
    
settings = Settings()

