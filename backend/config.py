import os
import platform
import sys
from pathlib import Path
from typing import Literal, List

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus
from src.utils import _platform
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment (maps NODE_ENV to internal values)
    node_env: Literal["dev", "prod", "development", "production"] = Field(default="dev")

    # Database
    database_url: str = Field(
        default="",
        description="Database connection URL (auto-constructed if empty)"
    )
    
    # PostgreSQL Settings
    postgres_username: str = Field(
        default="postgres",
        description="PostgreSQL username"
    )
    postgres_password: str = Field(
        default="password",
        description="PostgreSQL password"
    )
    postgres_db_name: str = Field(
        default="scanpro_db",
        description="PostgreSQL database name"
    )
    postgres_host: str = Field(
        default="localhost",
        description="PostgreSQL host"
    )
    postgres_port: str = Field(
        default="5432",
        description="PostgreSQL port"
    )

    # Server configuration
    backend_host: str = Field(default="127.0.0.1")

    # Debug mode
    debug: int = Field(default=0, env="DEBUG")

    log_level: str | None = Field(default=None)

    # CORS settings
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )

    # Model configuration
    # Hugging Face token for private models
    scanpro_hf_token: str = Field(default="")

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
        protected_namespaces = ("settings_",)
        extra = "allow"
        env_ignore_empty = True

    @property
    def node_env_value(self) -> str:
        """Map NODE_ENV environment variable to internal values."""
        import os

        env_value = os.getenv("NODE_ENV", "development")
        if env_value in ["production", "prod"]:
            return "prod"
        return "dev"

    @model_validator(mode='after')
    def construct_database_url(self):
        """Construct database URL if not provided"""
        if not self.database_url or self.database_url.strip() == "":           
            # Use PostgreSQL with environment settings
            if self.postgres_password:
                self.database_url = (
                    f"postgresql://{quote_plus(self.postgres_username)}:{quote_plus(self.postgres_password)}"
                    f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db_name}"
                )
            else:
                self.database_url = (
                    f"postgresql://{quote_plus(self.postgres_username)}"
                    f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db_name}"
                )
            logger.info(f"Using environment PostgreSQL: {self.database_url}")
        
        return self


# Application name (hardcoded)
APP_NAME = "ScanPro"

# Fixed ports inside container
BACKEND_PORT = 5000
FRONTEND_PORT = 3000

DB_ENGINE = "PostgreSQL"

# Create settings instance
settings = Settings()

# Environment checks
is_development = settings.node_env_value == "dev"
is_production = settings.node_env_value == "prod"

# Application directory logic
APP_DIR = Path(__file__).resolve().parent.parent / "APP_DATA"

# Core application paths
LOGS_DIR = APP_DIR / "logs"
DB_DIR = APP_DIR / "db"

# ML model paths (for inference only)
ML_MODELS_DIR = APP_DIR / "ml_models"
# CLASSIFIER_MODEL_PATH = ML_MODELS_DIR / "classifier_model"
CLASSIFIER_MODEL_ID = "bradenacurtis/scanpro-classifier-v1-finetune"

def setup_app_dirs():
    """Create all required application directories."""
    logger.debug("Creating application directories...")
    APP_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug("Application directories created successfully")

#######################################################
#######################################################

# Environment-specific logging configuration
if is_development:
    LOG_LEVEL = "DEBUG"
    ENABLE_FILE_LOGGING = True
    CONSOLE_LOG_LEVEL = "DEBUG"
elif settings.node_env in ["prod", "production"]:
    LOG_LEVEL = "INFO"
    ENABLE_FILE_LOGGING = True
    CONSOLE_LOG_LEVEL = "WARNING"  # Less verbose console in production
else:  # staging, test, etc.
    LOG_LEVEL = "WARNING"
    ENABLE_FILE_LOGGING = False
    CONSOLE_LOG_LEVEL = "WARNING"

# Override with explicit log_level setting if provided
LOG_LEVEL = settings.log_level if settings.log_level else LOG_LEVEL

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(threadName)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(threadName)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "app.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "": {
            "level": LOG_LEVEL,
            "handlers": ["console"] + (["file"] if ENABLE_FILE_LOGGING else [])
        },
        "app": {
            "level": LOG_LEVEL,
            "handlers": ["console"] + (["file"] if ENABLE_FILE_LOGGING else []),
            "propagate": False
        },
        "sqlalchemy": {
            "level": logging.ERROR,  # Only show SQL errors, not queries
            "handlers": ["console"] + (["file"] if ENABLE_FILE_LOGGING else []),
            "propagate": False
        },
        "uvicorn": {
            "level": logging.INFO,  # Keep server startup/shutdown info
            "handlers": ["console"] + (["file"] if ENABLE_FILE_LOGGING else []),
            "propagate": False
        },
        "uvicorn.access": {
            "level": logging.ERROR,  # Only show HTTP errors, not every request
            "handlers": ["console"] + (["file"] if ENABLE_FILE_LOGGING else []),
            "propagate": False
        },
        "httpx": {
            "level": logging.WARNING,  # External HTTP requests
            "handlers": ["console"] + (["file"] if ENABLE_FILE_LOGGING else []),
            "propagate": False
        },
        "websockets": {
            "level": logging.WARNING,  # WebSocket connection issues
            "handlers": ["console"] + (["file"] if ENABLE_FILE_LOGGING else []),
            "propagate": False
        }
    },
}
