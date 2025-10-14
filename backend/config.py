import os
import platform
import sys
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings
from src.utils import _platform


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment (maps NODE_ENV to internal values)
    node_env: Literal["dev", "prod", "development", "production"] = Field(default="dev")

    # Server configuration
    backend_host: str = Field(default="127.0.0.1", env="BACKEND_HOST")

    # Debug mode
    debug: int = Field(default=0, env="DEBUG")

    # CORS settings
    cors_origins: str = Field(default="http://127.0.0.1:3000", env="CORS_ORIGINS")

    # Model configuration
    model_url: str = Field(default="", env="SCANPRO_MODEL_URL")

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
        protected_namespaces = ("settings_",)

    @property
    def node_env_value(self) -> str:
        """Map NODE_ENV environment variable to internal values."""
        import os

        env_value = os.getenv("NODE_ENV", "development")
        if env_value in ["production", "prod"]:
            return "prod"
        return "dev"


# Application name (hardcoded)
APP_NAME = "ScanPro"

# Fixed ports inside container
BACKEND_PORT = 5000
FRONTEND_PORT = 3000

# Create settings instance
settings = Settings()

# Environment checks
is_development = settings.node_env_value == "dev"
is_production = settings.node_env_value == "prod"

# Application directory logic
APP_DIR = Path(__file__).resolve().parent.parent / "APP_DATA"

# if is_development:
#     APP_DIR = Path(__file__).resolve().parent.parent / "APP_DATA"
# elif _platform.WINDOWS:
#     _basedir = os.environ.get("APPDATA", os.path.expanduser("~"))
#     APP_DIR = Path(_basedir) / APP_NAME
# elif _platform.DARWIN:
#     APP_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
# elif _platform.LINUX:
#     APP_DIR = Path.home() / ".config" / APP_NAME
# else:
#     raise BaseException(f"Unsupported platform: {platform.system()}")

# Core application paths
UPLOAD_DIR = APP_DIR / "uploads"
INDEX_FILE = APP_DIR / "document_index.faiss"
METADATA_FILE = APP_DIR / "document_metadata.json"

# ML model paths (for inference only)
ML_MODELS_DIR = APP_DIR / "ml_models"
DEFAULT_MODEL_PATH = ML_MODELS_DIR / "classifier_model"


def validate_model_directory(model_path: str) -> bool:
    """
    Validate that a model directory contains all required files.

    Args:
        model_path: Path to the model directory

    Returns:
        bool: True if valid, False otherwise
    """
    model_dir = Path(model_path)

    if not model_dir.exists():
        return False

    required_files = ["model_metadata.json", "category_embeddings.json"]

    for file_name in required_files:
        if not (model_dir / file_name).exists():
            return False

    return True


def get_model_url() -> str:
    """
    Get the model URL for downloading in production.

    Returns:
        str: URL to download the model from
    """
    return settings.model_url


def get_model_download_dir() -> str:
    """
    Get the directory to download models to in production.

    Returns:
        str: Directory path for downloaded models (ML_MODELS_DIR)
    """
    return str(ML_MODELS_DIR)


#######################################################
#######################################################
