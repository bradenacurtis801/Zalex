import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
# Application name used across all components
APP_DIR = ROOT_DIR / "APP_DATA"

# Training data paths
TEST_DATA_DIR = ROOT_DIR / "test_data"
SPANISH_DATA_DIR = TEST_DATA_DIR / "es"
DOCUMENT_RAW_DIR = SPANISH_DATA_DIR / "document_raw"
DOCUMENT_DATASET_DIR = SPANISH_DATA_DIR / "document_dataset"
ML_MODELS_DIR = APP_DIR / "ml_models"
TRAINING_DATA_PATH = DOCUMENT_DATASET_DIR / "training_data.json"