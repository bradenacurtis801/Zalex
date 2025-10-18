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
from src.ml.classification.model_loader import load_pretrained_classifier
from src.ocr.factory import get_default_ocr_engine
from src.utils.document_processor import DocumentProcessor
from src.utils.model_downloader import ModelDownloader

logger = logging.getLogger(__name__)

_app_state = None


class AppState:
    """Centralized application state management."""

    def __init__(self):
        self.document_processor: DocumentProcessor = None
        self.metadata: list = []
        self.model: SentenceTransformer = None
        self.index: faiss.IndexFlatL2 = None
        self.dimension = None
        self.document_classifier = None
        self.category_metadata: dict = {}
        self.model_downloader: ModelDownloader = None
        self.ocr_engine = None

    def initialize(self):
        """Initialize all application components."""

        # Load Sentence Transformer model
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=config.ML_MODELS_DIR)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to load Sentence Transformer model: {e}")
            raise e

        # Initialize OCR engine
        try:
            self.ocr_engine = get_default_ocr_engine()
            self.ocr_engine.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {e}")
            raise e

        # Load FAISS index and metadata
        self.load_index_and_metadata()

        # Load category metadata
        self.load_category_metadata()

        # Initialize document classifier
        self.initialize_classifier()

        # Populate categories from model metadata if category_metadata is empty
        if (
            not self.category_metadata
            and self.document_classifier
            and self.document_classifier.is_initialized
        ):
            model_categories = self.document_classifier.get_supported_categories()
            for category in model_categories:
                if category not in self.category_metadata:
                    self.category_metadata[category] = {}
            logger.info(
                f"Initialized categories from model: {list(self.category_metadata.keys())}"
            )

        # Initialize document processor
        self.document_processor = DocumentProcessor(
            self.model,
            self.index,
            self.metadata,
            self.ocr_engine,
            self.document_classifier,
            self.category_metadata,
        )

        logger.info("Application state initialized successfully.")

    def load_index_and_metadata(self):
        """Initialize FAISS index and metadata for database-only operation."""
        logger.info("Initializing FAISS index for database-only operation.")
        self.index = faiss.IndexFlatL2(self.dimension)
        logger.info("FAISS index initialized.")
        
        logger.info("Initializing empty metadata list for database-only operation.")
        self.metadata = []

    def save_index_and_metadata(self):
        """No-op for database-only operation - data is stored in database."""
        logger.info("Skipping file-based save - using database-only storage.")

    def load_category_metadata(self):
        """Loads the category metadata from disk if it exists."""
        category_file = config.APP_DIR / "category_metadata.json"
        if os.path.exists(category_file) and os.path.getsize(category_file) > 0:
            logger.info(f"Loading category metadata from {category_file}")
            with open(category_file, "r", encoding="utf-8") as f:
                self.category_metadata = json.load(f)
            logger.info(
                f"Category metadata loaded. Contains {len(self.category_metadata)} categories."
            )
        else:
            logger.info(
                "No category metadata file found. Initializing empty structure."
            )
            # Initialize empty structure - categories will be populated from model metadata
            self.category_metadata = {}

    def save_category_metadata(self):
        """Saves the current category metadata to disk."""
        category_file = config.APP_DIR / "category_metadata.json"
        logger.info(f"Saving category metadata to {category_file}")
        with open(category_file, "w", encoding="utf-8") as f:
            json.dump(self.category_metadata, f, indent=4)
        logger.info("Category metadata saved successfully.")

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
                model_path_or_id=config.CLASSIFIER_MODEL_ID, token=hf_token
            )

            if self.document_classifier and self.document_classifier.is_initialized:
                logger.info("Hugging Face model loaded successfully.")
                model_info = self.document_classifier.get_model_info()
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
