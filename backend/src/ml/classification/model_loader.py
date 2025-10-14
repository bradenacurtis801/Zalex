"""
Model loader for pre-trained similarity-based classifiers.
"""

import logging
from pathlib import Path
from typing import Optional

import config

from .base_classifier import BaseDocumentClassifier
from .pretrained_classifier import PreTrainedSimilarityClassifier

logger = logging.getLogger(__name__)


def load_pretrained_classifier(
    model_dir: str,
) -> Optional[PreTrainedSimilarityClassifier]:
    """
    Load a pre-trained classifier from the specified directory.

    Args:
        model_dir: Path to the directory containing the trained model files

    Returns:
        PreTrainedSimilarityClassifier: Loaded classifier or None if failed
    """
    try:
        classifier = PreTrainedSimilarityClassifier()
        if classifier.load_model(model_dir):
            logger.info(f"Successfully loaded pre-trained classifier from {model_dir}")
            return classifier
        else:
            logger.error(f"Failed to load pre-trained classifier from {model_dir}")
            return None
    except Exception as e:
        logger.error(f"Error loading pre-trained classifier: {e}")
        return None
