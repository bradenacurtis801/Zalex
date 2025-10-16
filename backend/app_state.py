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
        logger.info("Initializing application state...")

        # Load Sentence Transformer model
        try:
            logger.info("Loading Sentence Transformer model...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info("Sentence Transformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Sentence Transformer model: {e}")
            raise e

        # Initialize OCR engine
        try:
            logger.info("Initializing OCR engine...")
            self.ocr_engine = get_default_ocr_engine()
            self.ocr_engine.initialize()
            logger.info("OCR engine initialized successfully.")
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
        """Loads the FAISS index and metadata from disk if they exist."""
        if os.path.exists(config.INDEX_FILE) and os.path.getsize(config.INDEX_FILE) > 0:
            logger.info(f"Loading FAISS index from {config.INDEX_FILE}")
            self.index = faiss.read_index(str(config.INDEX_FILE))
            logger.info(f"Index loaded. Contains {self.index.ntotal} vectors.")
        else:
            logger.info("No FAISS index found. Initializing a new one.")
            self.index = faiss.IndexFlatL2(self.dimension)

        if (
            os.path.exists(config.METADATA_FILE)
            and os.path.getsize(config.METADATA_FILE) > 0
        ):
            logger.info(f"Loading metadata from {config.METADATA_FILE}")
            with open(config.METADATA_FILE, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            logger.info(f"Metadata loaded. Contains {len(self.metadata)} entries.")
        else:
            logger.info("No metadata file found. Initializing empty list.")
            self.metadata = []

    def save_index_and_metadata(self):
        """Saves the current FAISS index and metadata to disk."""
        logger.info(f"Saving FAISS index to {config.INDEX_FILE}")
        faiss.write_index(self.index, str(config.INDEX_FILE))
        logger.info(f"Saving metadata to {config.METADATA_FILE}")
        with open(config.METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=4)
        logger.info("Index and metadata saved successfully.")

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
            hf_model_id = "bradenacurtis/scanpro-classifier-v1-finetune"
            logger.info(f"Loading model from Hugging Face: {hf_model_id}")
            hf_token = (
                config.settings.scanpro_hf_token
                if config.settings.scanpro_hf_token
                else None
            )

            # Create fine-tuned classifier from Hugging Face
            logger.info("Creating fine-tuned classifier from Hugging Face")
            self.document_classifier = PreTrainedFinetuneClassifier(
                model_path_or_id=hf_model_id, token=hf_token
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
