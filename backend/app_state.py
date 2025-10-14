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
from src.ml.classification.model_loader import load_pretrained_classifier
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
        self.model_path: str = None
        self.model_url: str = None
        self.model_downloader: ModelDownloader = None

    def set_model_path(self, model_path: str):
        """Set the model path for the application."""
        self.model_path = model_path
        logger.debug(f"Model path set to: {model_path}")

    def set_model_url(self, model_url: str):
        """Set the model URL for downloading in production."""
        self.model_url = model_url
        logger.debug(f"Model URL set to: {model_url}")

    def _get_model_directory(self) -> str:
        """
        Get the model directory path, either from local path or by downloading from URL.

        Returns:
            str: Path to the model directory, or None if not available
        """
        # First, try to use the configured local path
        if self.model_path and os.path.exists(self.model_path):
            if config.validate_model_directory(self.model_path):
                logger.debug(f"Using local model path: {self.model_path}")
                return self.model_path
            else:
                logger.warning(
                    f"Model directory exists but is invalid: {self.model_path}"
                )

        # Check if model exists in ML_MODELS_DIR (development default)
        default_model_path = str(config.DEFAULT_MODEL_PATH)
        if os.path.exists(default_model_path):
            if config.validate_model_directory(default_model_path):
                logger.info(f"Found valid model in ML_MODELS_DIR: {default_model_path}")
                # Set the model path for future reference
                self.model_path = default_model_path
                return default_model_path
            else:
                logger.warning(
                    f"Model directory exists but is invalid: {default_model_path}"
                )

        # If no local model found and no URL configured, return None
        if not self.model_url:
            logger.warning("No local model found and no model URL configured")
            logger.info("Please either:")
            logger.info(
                "  1. Train a model first: python train/train_similarity_classifier.py"
            )
            logger.info("  2. Set SCANPRO_MODEL_URL to download a model")
            logger.info(f"  3. Place a trained model in: {default_model_path}")
            logger.info(
                "     (must contain: model_metadata.json, category_embeddings.json)"
            )
            raise RuntimeError("No model path configured and no model URL provided")

        # Try to download from URL
        try:
            if not self.model_downloader:
                download_dir = config.get_model_download_dir()
                self.model_downloader = ModelDownloader(download_dir)

            # Check if model is already downloaded
            model_name = "classifier_model"
            if self.model_downloader.is_model_downloaded(model_name):
                model_path = self.model_downloader.get_model_path(model_name)
                if config.validate_model_directory(model_path):
                    logger.info(f"Using previously downloaded model: {model_path}")
                    # Set the model path for future reference
                    self.model_path = model_path
                    return model_path
                else:
                    logger.warning(
                        f"Downloaded model is invalid, will re-download: {model_path}"
                    )

                    # Download the model
                    logger.info(f"Downloading model from URL: {self.model_url}")
                    model_path = self.model_downloader.download_model(
                        self.model_url, model_name
                    )
                    if model_path and config.validate_model_directory(model_path):
                        logger.info(f"Model downloaded successfully to: {model_path}")
                        # Set the model path for future reference
                        self.model_path = model_path
                        return model_path
                    else:
                        logger.error(f"Downloaded model is invalid: {model_path}")
                        return None

        except Exception as e:
            logger.error(f"Failed to download model from URL: {e}")
            logger.error(
                "Please ensure the model URL is accessible and the model package is valid"
            )
            return None

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

        # Load FAISS index and metadata
        self.load_index_and_metadata()

        # Load category metadata
        self.load_category_metadata()

        # Initialize document classifier
        self.initialize_classifier()

        # Initialize document processor
        self.document_processor = DocumentProcessor(
            self.model,
            self.index,
            self.metadata,
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
            self.category_metadata = {
                "birth_certificate": [],
                "marriage_certificate": [],
                "property_deeds": [],
                "other": [],
            }

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

            # Determine model path (local or download from URL)
            model_dir = self._get_model_directory()

            if not model_dir:
                raise RuntimeError(
                    "No model directory found - cannot initialize classifier"
                )

            if not os.path.exists(model_dir):
                raise RuntimeError(
                    f"Model directory not found: {model_dir}. Please run the training script first: python train/train_similarity_classifier.py"
                )

            # Load the pre-trained classifier
            self.document_classifier = load_pretrained_classifier(model_dir)

            if self.document_classifier and self.document_classifier.is_available():
                logger.info("Pre-trained document classifier loaded successfully.")
                model_info = self.document_classifier.get_model_info()
                logger.info(f"Model info: {model_info}")
            else:
                raise RuntimeError("Failed to load pre-trained document classifier")

        except Exception as e:
            logger.error(f"Failed to initialize classifier: {e}")
            raise


def get_app_state():
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state
