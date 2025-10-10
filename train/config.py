import os
import sys
from pathlib import Path

#######################################################
###################### CONSTANTS ######################
#######################################################

# Application name used across all components
APP_DIR = Path(sys.argv[0]).resolve().parent / "APP_DATA"

# Training data paths
DOCUMENT_RAW_DIR = APP_DIR / "document_raw"
DOCUMENT_DATASET_DIR = APP_DIR / "document_dataset"

# ML model paths (for saving trained models)
ML_MODELS_DIR = APP_DIR / "ml_models"
SPANISH_CLASSIFIER_MODEL = ML_MODELS_DIR / "spanish_doc_classifier_model"

# ML training outputs
TRAINING_RESULTS_DIR = APP_DIR / "training_results"
TRAINING_LOGS_DIR = APP_DIR / "training_logs"


#######################################################
#######################################################
