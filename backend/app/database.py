"""Database initialization and setup."""

from app.models.base import Base, engine
from app.utils.logger import logger


def init_database():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


if __name__ == "__main__":
    init_database()