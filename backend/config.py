import os
from pathlib import Path
import platform
import sys

from src.utils import _platform

#######################################################
###################### CONSTANTS ######################
#######################################################

is_development = os.getenv('NODE_ENV', 'dev') == 'dev'
is_production = os.getenv('NODE_ENV', 'dev') == 'prod'

# Application name used across all components
APP_NAME = "ScanPro"

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
UPLOAD_DIR = APP_DIR / 'uploads'
INDEX_FILE = APP_DIR / 'document_index.faiss'
METADATA_FILE = APP_DIR / 'document_metadata.json'

# ML model paths (for inference only)
ML_MODELS_DIR = APP_DIR / 'ml_models'
SPANISH_CLASSIFIER_MODEL = ML_MODELS_DIR / 'spanish_doc_classifier_model'

# Create all directories
APP_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

#######################################################
#######################################################