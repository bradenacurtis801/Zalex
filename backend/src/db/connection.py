# app/database/connection.py
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import logging
import config
from src.core.constants import get_database_config

# Set up logger
logger = logging.getLogger(__name__)

# Get database configuration based on environment
db_config = get_database_config()

engine = create_engine(
    config.settings.database_url,
    echo=config.LOG_LEVEL == "DEBUG",
    **get_database_config()
)

def create_db_and_tables():
    """Create database tables"""
    logger.info(f"Creating {config.DB_ENGINE} database tables for environment")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")

def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    with Session(engine) as session:
        yield session