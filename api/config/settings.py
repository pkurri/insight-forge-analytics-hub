"""
Settings Configuration Module

This module provides centralized configuration management for the application.
"""

import os
from typing import Any, Dict
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional
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
    """Application settings class."""
    
    # API Settings
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Vector Store Settings
    VECTOR_DIMENSION: int = 384
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE_URL: str = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    OPENAI_API_TIMEOUT: int = int(os.getenv("OPENAI_API_TIMEOUT", "30"))
    OPENAI_API_MAX_RETRIES: int = int(os.getenv("OPENAI_API_MAX_RETRIES", "3"))
    
    # Allowed Models
    ALLOWED_TEXT_GEN_MODELS: list = [
        "gpt-3.5-turbo",
        "gpt-4",
        "Mistral-3.2-instruct"
    ]
    
    # Business Rules Settings
    RULE_EXECUTION_TIMEOUT: int = int(os.getenv("RULE_EXECUTION_TIMEOUT", "30"))
    MAX_RULES_PER_DATASET: int = int(os.getenv("MAX_RULES_PER_DATASET", "100"))
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "https://dataforge-analytics.com"]
    
    # Vector Database Settings
    VECTOR_DB_ENABLED: bool = os.getenv("VECTOR_DB_ENABLED", "True").lower() == "true"
    VECTOR_DIMENSION: int = 1536  # OpenAI embedding dimension
    
    # File Upload Settings
    UPLOAD_DIR: str = "api/uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # AI/ML Settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Only approved embedding and text generation models are supported. Translation API is not exposed.

    # Only internal Hugging Face module is used for embeddings/generation. Direct Hugging Face API is not supported.

    # Internal Text Generation API (Mistral, Llama, Pythia)
    INTERNAL_TEXT_GEN_API_URL: str = os.getenv("INTERNAL_TEXT_GEN_API_URL", "http://internal-api/models/generate")
    INTERNAL_TEXT_GEN_API_USER: str = os.getenv("INTERNAL_TEXT_GEN_API_USER", "")
    INTERNAL_TEXT_GEN_API_PASS: str = os.getenv("INTERNAL_TEXT_GEN_API_PASS", "")
    INTERNAL_TEXT_GEN_MODEL: str = os.getenv("INTERNAL_TEXT_GEN_MODEL", "mistral")
    VECTOR_EMBEDDING_API_ENDPOINT: str = os.getenv("VECTOR_EMBEDDING_API_ENDPOINT", "http://internal-api/models/generate")
    VECTOR_EMBEDDING_API_USERID: str = os.getenv("VECTOR_EMBEDDING_API_USERID", "")
    VECTOR_EMBEDDING_API_PASSWORD: str = os.getenv("VECTOR_EMBEDDING_API_PASSWORD", "")
    VECTOR_EMBEDDING_API_MODEL: str = os.getenv("VECTOR_EMBEDDING_API_MODEL", "mistral")
    VECTOR_EMBEDDING_API_KEY: str = os.getenv("VECTOR_EMBEDDING_API_KEY", "")
    # Logging Settings
    logging: LoggingSettings = LoggingSettings()

    # Allowed embedding and generation models (internal only)
    ALLOWED_EMBEDDING_MODELS: List[str] = [
        "all-MiniLM-L6-v2",
        "nomic-embed-text-v1.5",
        "roberta-base-go_emotions-SapBERT",
        "BioLinkBERT-large"
    ]
    ALLOWED_TEXT_GEN_MODELS: List[str] = [
        "Mistral-3.2-instruct",
        "llama-3.3-70b-instruct",
        "pythia28b"
    ]
    
    # Monitoring Settings
    ENABLE_MONITORING: bool = os.getenv("ENABLE_MONITORING", "True").lower() == "true"
    MONITORING_METRICS_RETENTION_DAYS: int = int(os.getenv("MONITORING_METRICS_RETENTION_DAYS", "30"))
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings instance
    """
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

def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a specific setting value.
    
    Args:
        key: Setting key to retrieve
        default: Default value if setting not found
        
    Returns:
        Any: Setting value or default
    """
    settings = get_settings()
    return getattr(settings, key, default)

def update_settings(settings_dict: Dict[str, Any]) -> None:
    """
    Update settings with new values.
    
    Args:
        settings_dict: Dictionary of settings to update
    """
    settings = get_settings()
    for key, value in settings_dict.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
