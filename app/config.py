"""Configuration management for AI Assistant System."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenRouter API Configuration
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    
    # Model Configuration
    default_model: str = Field("openrouter/horizon-beta", env="DEFAULT_MODEL")
    mistral_model: str = Field("mistralai/mistral-small-3.2-24b-instruct:free", env="MISTRAL_MODEL")
    qwen_model: str = Field("qwen/qwen3-coder:free", env="QWEN_MODEL")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./ai_assistant.db", env="DATABASE_URL")
    vector_db_path: str = Field("./vector_store", env="VECTOR_DB_PATH")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    debug: bool = Field(True, env="DEBUG")
    
    # Memory Configuration
    max_memory_size: int = Field(10000, env="MAX_MEMORY_SIZE")
    embedding_model: str = Field("all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # File Upload Configuration
    max_file_size: str = Field("50MB", env="MAX_FILE_SIZE")
    upload_dir: str = Field("./uploads", env="UPLOAD_DIR")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("./logs/ai_assistant.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()