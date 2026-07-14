"""Base LLM client interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, field_validator


class LLMResponse(BaseModel):
    """Standardized LLM response."""
    content: str
    model: str
    usage: Optional[Dict[str, Union[int, float]]] = None
    raw_response: Optional[Any] = None
    
    @field_validator('usage', mode='before')
    @classmethod
    def validate_usage(cls, v):
        """Convert float values to int where appropriate."""
        if v and isinstance(v, dict):
            # Convert float time values to int (milliseconds)
            for key in ['completion_time', 'prompt_time', 'queue_time', 'total_time']:
                if key in v and isinstance(v[key], (int, float)):
                    # Convert to int if it's a float
                    if isinstance(v[key], float):
                        v[key] = int(v[key] * 1000)  # Convert seconds to milliseconds
            # Ensure integer values for token counts
            for key in ['completion_tokens', 'prompt_tokens', 'total_tokens']:
                if key in v and isinstance(v[key], float):
                    v[key] = int(v[key])
        return v


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from chat history."""
        pass