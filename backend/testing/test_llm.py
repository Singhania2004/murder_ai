"""Test LLM clients."""

import asyncio
from app.models.llm.factory import LLMFactory
from app.utils.logger import logger


async def test_groq():
    """Test Groq client."""
    logger.info("Testing Groq client...")
    
    client = LLMFactory.get_primary()
    
    response = await client.generate(
        prompt="What is a murder mystery? Give a one-sentence answer.",
        system_prompt="You are a helpful assistant.",
        temperature=0.7
    )
    
    logger.info(f"Groq response: {response.content}")
    return response


async def main():
    """Run tests."""
    try:
        await test_groq()
    except Exception as e:
        logger.error(f"Groq test failed: {str(e)}")
    
    logger.info("Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())