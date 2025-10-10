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
    node_env: Literal["dev", "prod"] = Field(default="dev")

    # Server configuration
    backend_port: int = Field(default=5000, env="BACKEND_PORT")
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")

    # Debug mode
    debug: bool = Field(default=True, env="DEBUG")

    # CORS settings
    cors_origins: str = Field(default="http://localhost:3000", env="CORS_ORIGINS")

    class Config:
        case_sensitive = False

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

# Create settings instance
settings = Settings()

# Environment checks
is_development = settings.node_env_value == "dev"
is_production = settings.node_env_value == "prod"

# Application directory logic
APP_DIR: Path = Path("")

if is_development:
    APP_DIR = Path(sys.argv[0]).resolve().parent / "APP_DATA"
elif _platform.WINDOWS:
    _basedir = os.environ.get("APPDATA", os.path.expanduser("~"))
    APP_DIR = Path(_basedir) / APP_NAME
elif _platform.DARWIN:
    APP_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
elif _platform.LINUX:
    APP_DIR = Path.home() / ".config" / APP_NAME
else:
    raise BaseException(f"Unsupported platform: {platform.system()}")

# Core application paths
UPLOAD_DIR = APP_DIR / "uploads"
INDEX_FILE = APP_DIR / "document_index.faiss"
METADATA_FILE = APP_DIR / "document_metadata.json"

# ML model paths (for inference only)
ML_MODELS_DIR = APP_DIR / "ml_models"
SPANISH_CLASSIFIER_MODEL = ML_MODELS_DIR / "spanish_doc_classifier_model"

# Create all directories
APP_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

#######################################################
#######################################################
