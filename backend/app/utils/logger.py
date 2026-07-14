"""Logging configuration."""

from loguru import logger
import sys


def setup_logger():
    """Configure Loguru logger."""
    logger.remove()  # Remove default handler
    
    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # File logging for debugging
    logger.add(
        "logs/game_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level="DEBUG"
    )
    
    return logger


# Initialize logger
logger = setup_logger()