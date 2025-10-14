import os
import sys
from pathlib import Path

#######################################################
###################### CONSTANTS ######################
#######################################################

ROOT_DIR = Path(__file__).resolve().parent.parent
# Application name used across all components
APP_DIR = ROOT_DIR / "APP_DATA"

# Training data paths
TEST_DATA_DIR = ROOT_DIR / "test_data"
SPANISH_DATA_DIR = TEST_DATA_DIR / "es"
DOCUMENT_RAW_DIR = SPANISH_DATA_DIR / "document_raw"
DOCUMENT_DATASET_DIR = SPANISH_DATA_DIR / "document_dataset"

# ML model paths (for saving trained models)
ML_MODELS_DIR = APP_DIR / "ml_models"
CLASSIFIER_MODEL = ML_MODELS_DIR / "classifier_model"

# ML training outputs
TRAINING_RESULTS_DIR = APP_DIR / "training_results"
TRAINING_LOGS_DIR = APP_DIR / "training_logs"


#######################################################
#######################################################
