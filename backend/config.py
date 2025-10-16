import os
import platform
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
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
    # Hugging Face token for private models
    scanpro_hf_token: str = Field(default="")

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
# CLASSIFIER_MODEL_PATH = ML_MODELS_DIR / "classifier_model"
CLASSIFIER_MODEL_PATH = ML_MODELS_DIR / "finetune_classifier"

#######################################################
#######################################################
