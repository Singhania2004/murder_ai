"""Check available Groq models."""

import os
from groq import Groq
from app.config import settings
from app.utils.logger import logger

def check_models():
    """Check available models from Groq."""
    try:
        client = Groq(api_key=settings.groq_api_key)
        
        # List available models
        models = client.models.list()
        
        logger.info("Available Groq models:")
        for model in models.data:
            logger.info(f"  - {model.id} (active: {model.active})")
            
        return models
    except Exception as e:
        logger.error(f"Error checking models: {str(e)}")
        return None

if __name__ == "__main__":
    check_models()