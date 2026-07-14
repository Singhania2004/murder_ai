"""Base agent class for all agents."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from app.models.llm.base import BaseLLMClient, LLMResponse
from app.models.llm.factory import LLMFactory
from app.utils.logger import logger


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(
        self,
        name: str,
        role: str,
        model_type: str = "primary",
        system_prompt: Optional[str] = None
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = LLMFactory.get_client(model_type)
        self.conversation_history = []
        logger.info(f"Initialized agent: {name} ({role})")
    
    @abstractmethod
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process input and return response."""
        pass
    
    async def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Call the LLM with the given prompt."""
        system = system_prompt or self.system_prompt
        return await self.llm.generate(
            prompt=prompt,
            system_prompt=system,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    async def _call_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Call the LLM with chat history."""
        return await self.llm.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()