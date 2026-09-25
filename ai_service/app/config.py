"""Configuration settings for AI Service"""
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict
import os
import json
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Service settings
    DEBUG: bool = False
    SERVICE_NAME: str = "Smart Health AI Service"
    
    # Ollama settings (DISABLED - using local fine-tuned models instead)
    OLLAMA_HOST: str = "http://localhost:11434"  # Dummy - Ollama not used
    OLLAMA_MODEL: str = "DoctorHub-medical-ft"  # Custom fine-tuned medical model
    AUTO_PULL_MODEL: bool = False  # Don't auto-pull, we use custom model

    # Dynamic Fine-tuned Model Settings
    ADAPTER_PATH: Optional[str] = "app/ai_model"
    USE_QUANTIZATION: bool = False
    MAX_SEQ_LENGTH: int = 4096
    
    AI_MODEL_PATH: str = "app/ai_model"
    USE_QUANTIZATION: bool = True           # اگر می‌خواهید 4-bit بگذارید True
    MAX_SEQ_LENGTH: int = 4096               # طول توالی ورودی
    TOP_P: float = 0.9 
    LORA_MODEL_PATH: str = "app/ai_model"
    USE_FINE_TUNED: bool = True
    
    BASE_MODEL_PATH: Optional[str] = None
    
    FINETUNED_MODELS: Dict[str, str] = {
        "medical": "app/ai_model",
        "gemma_270m": "app/ai_model",
    }
    
    DEFAULT_MODEL_NAME: str = "medical"

    GEMMA_270M_BASE: str = "google/gemma-3-270m"
    GEMMA_2B_BASE: str = "unsloth/gemma-2-2b-bnb-4bit"
    GEMMA_4B_BASE: str = "google/gemma-2b"
    
    ENABLE_PHI_SCRUBBING: bool = True
    AUDIT_LOG_PATH: str = "logs/ai_audit.log"

    # CORS origins as string - parsed in main.py to avoid pydantic env parsing issues
    ALLOWED_ORIGINS: str = "http://magggicai-magicai.runflare.run,http://magggicai-magicai.runflare.run,http://magicai.runflare.run,http://magicai.runflare.run,http://maggicaihub.com:3000,http://maggicaihub.com:3000,http://127.0.0.1:3000,http://localhost:5000"
    
    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """Parse comma-separated origins string to list."""
        return [x.strip() for x in self.ALLOWED_ORIGINS.split(",") if x.strip()]
    
    REDIS_HOST: str = "redis.runflare.local"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2000
    TOP_P: float = 0.9
    
    AI_PROVIDER: str = "local"

    # POSTGRES_USER: str = "postgres"
    # POSTGRES_PASSWORD: str = "ppIdIZfPaBTFn5h1v8kx"
    # POSTGRES_HOST: str = "db.runflare.local"
    # POSTGRES_PORT: int = 32686
    # POSTGRES_DB: str = "postgreshif_db"
    
    # @property
    # def SQLALCHEMY_DATABASE_URL(self) -> str:
    #     return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 3


settings = Settings()

