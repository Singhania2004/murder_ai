"""Configuration management for the application."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    
    # Model Configuration - Using confirmed working models
    primary_model: str = Field("groq/llama-3.3-70b-versatile", env="PRIMARY_MODEL")
    forensic_model: str = Field("groq/llama-3.1-8b-instant", env="FORENSIC_MODEL")
    suspect_model: str = Field("groq/llama-3.3-70b-versatile", env="SUSPECT_MODEL")
    
    # Game Settings
    max_accusations: int = Field(3, env="MAX_ACCUSATIONS")
    time_limit: int = Field(900, env="TIME_LIMIT")  # seconds
    default_suspects: int = Field(4, env="DEFAULT_SUSPECTS")
    default_witnesses: int = Field(2, env="DEFAULT_WITNESSES")
        
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()