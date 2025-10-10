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
from src.services.document_processor import DocumentProcessor

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

        # Initialize document processor
        self.document_processor = DocumentProcessor(
            self.model, self.index, self.metadata
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


def get_app_state():
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state
