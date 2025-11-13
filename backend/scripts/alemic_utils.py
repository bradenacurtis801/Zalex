from alembic.config import Config
from alembic import command
from pathlib import Path
import logging

from src.db.connection import create_db_and_tables

logger = logging.getLogger(__name__)


def run_migrations():
    try:
        import config
        alembic_cfg = Config(str(config.ALEMBIC_INI_PATH))
        # Set the script location to absolute path (relative to backend directory)
        backend_dir = Path(__file__).parent
        alembic_cfg.set_main_option("script_location", str(backend_dir / "migrations"))
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database migrations completed")
    except Exception as e:
        logger.warning(f"Migration failed (this is OK if tables don't exist yet): {e}")
        create_db_and_tables()