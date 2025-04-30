
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import logging.config
import json

# Load environment variables from .env file
load_dotenv()

class LoggingSettings(BaseSettings):
    LOGGING_LEVEL: str = os.getenv("LOGGING_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    LOG_TO_CONSOLE: bool = os.getenv("LOG_TO_CONSOLE", "True").lower() == "true"

class Settings(BaseSettings):
    # API Settings
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "DataForge Analytics API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "https://dataforge-analytics.com"]
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/dataforge")
    
    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecretkey")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Vector Database Settings
    VECTOR_DB_ENABLED: bool = os.getenv("VECTOR_DB_ENABLED", "True").lower() == "true"
    VECTOR_DIMENSION: int = 1536  # OpenAI embedding dimension
    
    # File Upload Settings
    UPLOAD_DIR: str = "api/uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # AI/ML Settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Only approved embedding and text generation models are supported. Translation API is not exposed.

    # Hugging Face API Settings
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    HF_API_BASE: str = os.getenv("HF_API_BASE", "https://api-inference.huggingface.co/models/")
    HF_MODEL_NAME: str = os.getenv("HF_MODEL_NAME", "distilbert-base-uncased")

    # Internal Text Generation API (Mistral, Llama, Pythia)
    INTERNAL_TEXT_GEN_API_URL: str = os.getenv("INTERNAL_TEXT_GEN_API_URL", "http://internal-api/models/generate")
    INTERNAL_TEXT_GEN_API_USER: str = os.getenv("INTERNAL_TEXT_GEN_API_USER", "")
    INTERNAL_TEXT_GEN_API_PASS: str = os.getenv("INTERNAL_TEXT_GEN_API_PASS", "")
    INTERNAL_TEXT_GEN_MODEL: str = os.getenv("INTERNAL_TEXT_GEN_MODEL", "mistral")
    
    # Logging Settings
    logging: LoggingSettings = LoggingSettings()

    # Allowed embedding and generation models
    ALLOWED_EMBEDDING_MODELS: List[str] = [
        "all-MiniLM-L6-v2",
        "nomic-embed-text-v1.5",
        "roberta-base-go_emotions-SapBERT",
        "BioLinkBERT-large"
    ]
    ALLOWED_TEXT_GEN_MODELS: List[str] = [
        "Mistral-3.2-instruct",
        "Llama-3.3-70b-instruct",
        "pythia28B"
    ]
    
    # Monitoring Settings
    ENABLE_MONITORING: bool = os.getenv("ENABLE_MONITORING", "True").lower() == "true"
    MONITORING_METRICS_RETENTION_DAYS: int = int(os.getenv("MONITORING_METRICS_RETENTION_DAYS", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    
    # Configure logging
    configure_logging(settings.logging)
    
    return settings

def configure_logging(logging_settings: LoggingSettings) -> None:
    """Configure logging based on settings."""
    handlers = {}
    
    if logging_settings.LOG_TO_CONSOLE:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": logging_settings.LOGGING_LEVEL,
        }
    
    if logging_settings.LOG_FILE:
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": logging_settings.LOG_FILE,
            "formatter": "standard",
            "level": logging_settings.LOGGING_LEVEL,
        }
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": logging_settings.LOG_FORMAT,
            },
        },
        "handlers": handlers,
        "loggers": {
            "": {  # root logger
                "handlers": list(handlers.keys()),
                "level": logging_settings.LOGGING_LEVEL,
            },
            "api": {
                "handlers": list(handlers.keys()),
                "level": logging_settings.LOGGING_LEVEL,
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(logging_config)
