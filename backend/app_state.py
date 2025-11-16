"""
Application state management for ScanPro.
Centralizes all app-wide state and services.
"""

import json
import logging
import os
import queue
from typing import TYPE_CHECKING, Optional

import config as config
import faiss
import sys
from sentence_transformers import SentenceTransformer
# from src.ml.classification.finetune_classifier import PreTrainedFinetuneClassifier
from src.ml.classification.tfidf_classifier import PreTrainedTFIDFClassifier
from scanpro_lib.ocr.factory import get_default_ocr_engine
from src.ml.faiss.embeddings import get_embeddings_index
from src.services.document_processing_service import DocumentProcessingService
from src.ml.faiss.embeddings import EmbeddingsIndex
from scanpro_lib.ocr import OCREngine
from src.ml.classification.base_classifier import DocumentClassifier
from src.ml.ner.base_ner import NERModel

logger = logging.getLogger(__name__)

_app_state = None

"""
To install the spaCy model, run the following command:
pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.7.0/es_core_news_sm-3.7.0-py3-none-any.whl
"""


class AppState:
    """Centralized application state management."""

    def __init__(self):
        self.metadata: list = []
        self.model: SentenceTransformer = None
        self.index: faiss.IndexFlatL2 = None
        self.dimension: int = None
        self.document_classifier: DocumentClassifier = None
        self.ner_model: Optional[NERModel] = None
        self.ocr_engine: OCREngine = None
        self.embeddings_index: Optional[EmbeddingsIndex] = None
        self.document_processing_service: DocumentProcessingService = None

    def initialize(self):
        """Initialize all application components."""
        try:

            # Load Sentence Transformer model
            self.model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=config.ML_MODELS_DIR)
            self.dimension = self.model.get_sentence_embedding_dimension()

            # Initialize FAISS embeddings index
            logger.info("Initializing FAISS embeddings index...")
            self.embeddings_index = get_embeddings_index(
                transformer=self.model,
                index_path=config.FAISS_INDEX_PATH,
            )
            # Get dimension from model for embeddings index
            logger.info(f"FAISS embeddings index initialized with dimension {self.dimension}")

            # Initialize OCR engine
            self.ocr_engine = get_default_ocr_engine()
            self.ocr_engine.initialize()

            # Initialize document classifier
            self.initialize_classifier()

            # Initialize NER model
            self.initialize_ner_model()

            logger.info("Application state initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize application state: {e}")
            sys.exit(1)


    def initialize_classifier(self):
        """Load a pre-trained document classifier for inference."""
        logger.info("Loading pre-trained document classifier...")

        # Try to load from hardcoded Hugging Face model first
        logger.info(f"Loading model from Hugging Face: {config.TFIDF_CLASSIFIER_MODEL_ID}")
        hf_token = (
            config.settings.scanpro_hf_token
            if config.settings.scanpro_hf_token
            else None
        )

        # Create fine-tuned classifier from Hugging Face
        logger.info("Creating fine-tuned classifier from Hugging Face")
        self.document_classifier = PreTrainedTFIDFClassifier(
            model_name_or_path=config.TFIDF_CLASSIFIER_MODEL_ID, 
            cache_folder=config.ML_MODELS_DIR, 
            token=hf_token
        )

        if self.document_classifier and self.document_classifier.is_initialized:
            logger.info("Hugging Face model loaded successfully.")
            model_info = self.document_classifier.get_classifier_info()
            logger.info(f"Model info: {model_info}")
            return


    def initialize_ner_model(self):
        """Load a NER model for entity extraction."""
        logger.info("Initializing NER model...")
        
        from src.ml.ner.spacy_ner import SpacyNERModel
        
        # Initialize spaCy NER model (defaults to Spanish small model)
        # Can be configured via environment variable or config
        ner_model_name = getattr(config.settings, 'ner_model_name', 'es_core_news_sm')
        
        self.ner_model = SpacyNERModel(
            model_name_or_path=ner_model_name,
        )

        self.ner_model.initialize()
        
        # Initialize the model
        logger.info("NER model initialized successfully.")
        model_info = self.ner_model.get_model_info()
        logger.info(f"NER model info: {model_info}")

                


def get_app_state():
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state
