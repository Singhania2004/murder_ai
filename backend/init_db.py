"""Initialize the database."""

from app.database import init_database
from app.utils.logger import logger

if __name__ == "__main__":
    logger.info("Initializing database...")
    init_database()
    logger.info("Database initialization complete!")