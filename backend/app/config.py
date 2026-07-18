"""Configuration management for the application."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    
    # Model Configuration - Using confirmed working models
    primary_model: str = "groq/llama-3.3-70b-versatile"
    forensic_model: str = "groq/llama-3.1-8b-instant"
    suspect_model: str = "groq/llama-3.3-70b-versatile"
    
    # Game Settings
    max_accusations: int = 1
    default_suspects: int = 4
    default_witnesses: int = 2
        
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()