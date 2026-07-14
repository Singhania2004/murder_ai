"""LLM Client Factory."""

from typing import Optional
from app.models.llm.base import BaseLLMClient
from app.models.llm.groq_client import GroqClient
from app.config import settings
from app.utils.logger import logger


class LLMFactory:
    """Factory for creating LLM clients."""
    
    _clients = {}
    
    @classmethod
    def get_client(
        cls,
        model_type: str = "primary",
        model_name: Optional[str] = None
    ) -> BaseLLMClient:
        """Get or create an LLM client."""
        key = f"{model_type}:{model_name or 'default'}"
        
        if key not in cls._clients:
            if model_type == "primary" or model_type == "groq":
                model = model_name or settings.primary_model
                cls._clients[key] = GroqClient(model)
            elif model_type == "suspect":
                model = model_name or settings.suspect_model
                cls._clients[key] = GroqClient(model)
            elif model_type == "forensic":
                model = model_name or settings.forensic_model
                cls._clients[key] = GroqClient(model)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
        
        return cls._clients[key]
    
    @classmethod
    def get_primary(cls, model_name: Optional[str] = None) -> BaseLLMClient:
        """Get primary LLM client."""
        return cls.get_client("primary", model_name)
    
    @classmethod
    def get_suspect(cls, model_name: Optional[str] = None) -> BaseLLMClient:
        """Get suspect LLM client."""
        return cls.get_client("suspect", model_name)
    
    @classmethod
    def get_forensic(cls, model_name: Optional[str] = None) -> BaseLLMClient:
        """Get forensic LLM client."""
        return cls.get_client("forensic", model_name)