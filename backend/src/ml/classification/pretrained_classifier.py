"""
Pre-trained similarity-based classifier for inference.
Uses SentenceTransformer embeddings with cosine similarity for classification.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
import numpy as np
from sentence_transformers import SentenceTransformer

from .base_classifier import BaseDocumentClassifier, DocumentClassificationResult

logger = logging.getLogger(__name__)


class PreTrainedSimilarityClassifier(BaseDocumentClassifier):
    """
    Pre-trained similarity-based classifier for inference only.
    Loads a trained model and provides classification functionality.
    Uses SentenceTransformer embeddings with cosine similarity.
    """

    def __init__(self, name: str = "Pre-trained Similarity Classifier"):
        super().__init__(name)
        self.model: Optional[SentenceTransformer] = None
        self.category_embeddings: Dict[str, np.ndarray] = {}
        self.model_name: str = ""
        self.is_initialized = False

    def load_model(self, model_dir: Optional[str] = None) -> bool:
        """
        Load a pre-trained model from disk.

        Args:
            model_dir: Directory containing the trained model files (optional, uses config if not provided)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use provided path or get from config
            if model_dir is None:
                model_dir = str(config.DEFAULT_MODEL_PATH)

            model_path = Path(model_dir)

            # Validate model directory
            if not config.validate_model_directory(model_dir):
                logger.error(f"Invalid model directory: {model_dir}")
                return False

            # Load metadata
            metadata_file = model_path / "model_metadata.json"
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            self.model_name = metadata.get("model_name", "unknown")
            categories = metadata.get("categories", [])

            # Load category embeddings
            embeddings_file = model_path / "category_embeddings.json"
            with open(embeddings_file, "r", encoding="utf-8") as f:
                embeddings_data = json.load(f)

            # Convert lists back to numpy arrays
            self.category_embeddings = {}
            for category, embedding_list in embeddings_data.items():
                if category in categories:
                    self.category_embeddings[category] = np.array(embedding_list)

            # Load the sentence transformer model
            self.model = SentenceTransformer(self.model_name)

            self.is_initialized = True
            logger.info(f"Successfully loaded pre-trained model: {self.model_name}")
            logger.info(f"Categories: {list(self.category_embeddings.keys())}")
            return True

        except Exception as e:
            logger.error(f"Failed to load pre-trained model: {e}")
            return False

    def initialize(self) -> bool:
        """Initialize the classifier by loading the model."""
        return self.load_model()

    def get_supported_categories(self) -> List[str]:
        """Get list of supported categories."""
        return list(self.category_embeddings.keys())

    def is_available(self) -> bool:
        """Check if classifier is available for use."""
        return self.is_initialized and self.model is not None

    def classify(self, text: str, filename: str = None) -> DocumentClassificationResult:
        """
        Classify text using pre-trained embeddings.

        Args:
            text: Input text to classify
            filename: Optional filename for context

        Returns:
            DocumentClassificationResult: Classification result
        """
        if not self.is_available():
            return DocumentClassificationResult(
                category="unknown",
                confidence=0.0,
                method="similarity",
                details={"error": "Classifier not available"},
            )

        try:
            # Generate embedding for input text
            text_embedding = self.model.encode([text], convert_to_tensor=False)[0]

            # Calculate similarities with category embeddings
            similarities = {}
            for category, category_embedding in self.category_embeddings.items():
                # Calculate cosine similarity
                similarity = np.dot(text_embedding, category_embedding) / (
                    np.linalg.norm(text_embedding) * np.linalg.norm(category_embedding)
                )
                similarities[category] = float(similarity)

            # Find best category
            if similarities:
                best_category = max(similarities, key=similarities.get)
                best_confidence = similarities[best_category]
            else:
                best_category = "unknown"
                best_confidence = 0.0

            return DocumentClassificationResult(
                category=best_category,
                confidence=best_confidence,
                method="similarity",
                details={
                    "similarities": similarities,
                    "model_name": self.model_name,
                    "filename": filename,
                },
            )

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return DocumentClassificationResult(
                category="unknown",
                confidence=0.0,
                method="similarity",
                details={"error": str(e)},
            )

    def get_available_categories(self) -> list:
        """Get list of available categories (alias for get_supported_categories)."""
        return self.get_supported_categories()

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "categories": self.get_supported_categories(),
            "is_initialized": self.is_initialized,
            "type": "PreTrainedSimilarityClassifier",
        }
