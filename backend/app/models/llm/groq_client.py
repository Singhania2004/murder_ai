"""Groq API client implementation."""

import os
from typing import Optional, List, Dict, Any
from groq import Groq, AsyncGroq
from app.models.llm.base import BaseLLMClient, LLMResponse
from app.config import settings
from app.utils.logger import logger


class GroqClient(BaseLLMClient):
    """Groq API client."""
    
    def __init__(self, model: str = None):
        self.model = model or settings.primary_model
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        # Extract model name (remove "groq/" prefix if present)
        self.model_name = self.model.replace("groq/", "")
        logger.info(f"Initialized Groq client with model: {self.model_name}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from a prompt."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat(messages, temperature, max_tokens, **kwargs)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from chat history."""
        try:
            logger.debug(f"Calling Groq with model: {self.model_name}")
            logger.debug(f"Messages: {messages}")
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extract usage data safely
            usage_data = None
            if response.usage:
                usage_dict = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                # Add time metrics if available
                if hasattr(response.usage, 'completion_time'):
                    usage_dict["completion_time"] = response.usage.completion_time
                if hasattr(response.usage, 'prompt_time'):
                    usage_dict["prompt_time"] = response.usage.prompt_time
                if hasattr(response.usage, 'queue_time'):
                    usage_dict["queue_time"] = response.usage.queue_time
                if hasattr(response.usage, 'total_time'):
                    usage_dict["total_time"] = response.usage.total_time
                usage_data = usage_dict
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=usage_data,
                raw_response=response
            )
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise