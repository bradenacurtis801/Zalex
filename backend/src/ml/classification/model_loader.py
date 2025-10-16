"""
Model loader for pre-trained classifiers.
Supports both similarity-based and fine-tuned classifiers.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Union

import config

from .base_classifier import BaseDocumentClassifier
from .finetune_classifier import PreTrainedFinetuneClassifier
from .similarity_classifier import PreTrainedSimilarityClassifier

logger = logging.getLogger(__name__)


def load_pretrained_classifier(
    model_dir: str,
) -> Optional[Union[PreTrainedSimilarityClassifier, PreTrainedFinetuneClassifier]]:
    """
    Load a pre-trained classifier from the specified directory.
    Automatically detects whether it's a similarity-based or fine-tuned classifier.

    Args:
        model_dir: Path to the directory containing the trained model files

    Returns:
        Loaded classifier or None if failed
    """
    try:
        model_path = Path(model_dir)

        # Check if it's a fine-tuned classifier (has config.json and model.safetensors)
        if "finetune_classifier" in str(model_path):
            logger.info("Detected fine-tuned classifier")
            classifier = PreTrainedFinetuneClassifier(model_dir)
            success = classifier.load_model()
        else:
            # Default to similarity classifier
            logger.info("Detected similarity-based classifier")
            classifier = PreTrainedSimilarityClassifier()
            success = classifier.load_model(model_dir)

        if success:
            logger.info(f"Successfully loaded pre-trained classifier from {model_dir}")
            return classifier
        else:
            logger.error(f"Failed to load pre-trained classifier from {model_dir}")
            return None
    except Exception as e:
        logger.error(f"Error loading pre-trained classifier: {e}")
        return None


def load_similarity_classifier(
    model_dir: str,
) -> Optional[PreTrainedSimilarityClassifier]:
    """
    Load a similarity-based classifier from the specified directory.

    Args:
        model_dir: Path to the directory containing the trained model files

    Returns:
        PreTrainedSimilarityClassifier: Loaded classifier or None if failed
    """
    try:
        classifier = PreTrainedSimilarityClassifier()
        if classifier.load_model(model_dir):
            logger.info(f"Successfully loaded similarity classifier from {model_dir}")
            return classifier
        else:
            logger.error(f"Failed to load similarity classifier from {model_dir}")
            return None
    except Exception as e:
        logger.error(f"Error loading similarity classifier: {e}")
        return None


def load_finetune_classifier(model_dir: str) -> Optional[PreTrainedFinetuneClassifier]:
    """
    Load a fine-tuned classifier from the specified directory.

    Args:
        model_dir: Path to the directory containing the trained model files

    Returns:
        PreTrainedFinetuneClassifier: Loaded classifier or None if failed
    """
    try:
        classifier = PreTrainedFinetuneClassifier(model_dir)
        if classifier.load_model():
            logger.info(f"Successfully loaded fine-tuned classifier from {model_dir}")
            return classifier
        else:
            logger.error(f"Failed to load fine-tuned classifier from {model_dir}")
            return None
    except Exception as e:
        logger.error(f"Error loading fine-tuned classifier: {e}")
        return None
