"""
Application state management for ScanPro.
Centralizes all app-wide state and services.
"""

import json
import logging
import os

import config as config
import faiss
from sentence_transformers import SentenceTransformer
from src.ml.classification.finetune_classifier import PreTrainedFinetuneClassifier
from src.ocr.factory import get_default_ocr_engine
from src.ml.faiss.embeddings import get_embeddings_index

logger = logging.getLogger(__name__)

_app_state = None


class AppState:
    """Centralized application state management."""

    def __init__(self):
        self.metadata: list = []
        self.model: SentenceTransformer = None
        self.index: faiss.IndexFlatL2 = None
        self.dimension = None
        self.document_classifier = None
        self.ocr_engine = None
        self.embeddings_index = None

    def initialize(self):
        """Initialize all application components."""

        # Load Sentence Transformer model
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=config.ML_MODELS_DIR)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to load Sentence Transformer model: {e}")
            raise e

        # Initialize FAISS embeddings index
        try:
            logger.info("Initializing FAISS embeddings index...")
            self.embeddings_index = get_embeddings_index(
                transformer=self.model,
                index_path=config.FAISS_INDEX_PATH,
            )
            # Get dimension from model for embeddings index
            logger.info(f"FAISS embeddings index initialized with dimension {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS embeddings index: {e}")
            raise e

        # Initialize OCR engine
        try:
            self.ocr_engine = get_default_ocr_engine()
            self.ocr_engine.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {e}")
            raise e

        # Initialize document classifier
        self.initialize_classifier()


        logger.info("Application state initialized successfully.")


    def initialize_classifier(self):
        """Load a pre-trained document classifier for inference."""
        try:
            logger.info("Loading pre-trained document classifier...")

            # Try to load from hardcoded Hugging Face model first
            logger.info(f"Loading model from Hugging Face: {config.CLASSIFIER_MODEL_ID}")
            hf_token = (
                config.settings.scanpro_hf_token
                if config.settings.scanpro_hf_token
                else None
            )

            # Create fine-tuned classifier from Hugging Face
            logger.info("Creating fine-tuned classifier from Hugging Face")
            self.document_classifier = PreTrainedFinetuneClassifier(
                model_name_or_path=config.CLASSIFIER_MODEL_ID, 
                cache_folder=config.ML_MODELS_DIR, 
                token=hf_token
            )

            if self.document_classifier and self.document_classifier.is_initialized:
                logger.info("Hugging Face model loaded successfully.")
                model_info = self.document_classifier.get_classifier_info()
                logger.info(f"Model info: {model_info}")
                return

        except Exception as e:
            logger.error(f"Failed to initialize classifier: {e}")
            raise


def get_app_state():
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state
