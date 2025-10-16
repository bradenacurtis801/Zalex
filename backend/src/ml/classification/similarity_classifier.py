"""
Pre-trained similarity-based classifier for inference.
Uses SentenceTransformer embeddings with cosine similarity for classification.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import config
import numpy as np
from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from ...models.feedback import CorrectionData

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

    @staticmethod
    def validate_model_directory(model_path: str) -> bool:
        """
        Validate that a model directory contains all required files for similarity classifier.

        Args:
            model_path: Path to the model directory

        Returns:
            bool: True if valid, False otherwise
        """
        model_dir = Path(model_path)

        if not model_dir.exists():
            return False

        required_files = ["model_metadata.json", "category_embeddings.json"]

        for file_name in required_files:
            if not (model_dir / file_name).exists():
                return False

        return True

    def load_model(self, model_dir: Optional[str] = None) -> bool:
        """
        Load a pre-trained model from disk.

        Args:
            model_dir: Directory containing the trained model files (optional, uses config if not provided)

        Returns:
            bool: True if successful, False otherwise

        Raises:
            InvalidModelDirectoryError: If the model directory is invalid or missing required files
        """
        try:
            # Use provided path or get from config
            if model_dir is None:
                model_dir = str(config.CLASSIFIER_MODEL_PATH)

            model_path = Path(model_dir)

            # Validate model directory
            if not self.validate_model_directory(model_dir):
                from ...core.exceptions import InvalidModelDirectoryError

                raise InvalidModelDirectoryError(
                    f"Invalid similarity classifier model directory: {model_dir}. "
                    f"Required files: model_metadata.json, category_embeddings.json"
                )

            # Load metadata
            metadata_file = model_path / "model_metadata.json"
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Validate required metadata fields
            required_fields = ["model_name", "categories"]
            missing_fields = [
                field for field in required_fields if field not in metadata
            ]
            if missing_fields:
                from ...core.exceptions import InvalidModelMetadataError

                raise InvalidModelMetadataError(
                    f"Missing required fields in model_metadata.json: {missing_fields}. "
                    f"Required fields: {required_fields}"
                )

            # Validate categories is not empty
            categories = metadata.get("categories", [])
            if not categories or not isinstance(categories, list):
                from ...core.exceptions import InvalidModelMetadataError

                raise InvalidModelMetadataError(
                    f"Invalid or empty 'categories' field in model_metadata.json. "
                    f"Expected non-empty list, got: {categories}"
                )

            self.model_name = metadata["model_name"]

            # Load category embeddings
            embeddings_file = model_path / "category_embeddings.json"
            with open(embeddings_file, "r", encoding="utf-8") as f:
                embeddings_data = json.load(f)

            # Validate embeddings data
            if not isinstance(embeddings_data, dict):
                from ...core.exceptions import InvalidModelMetadataError

                raise InvalidModelMetadataError(
                    f"Invalid category_embeddings.json format. Expected dictionary, got: {type(embeddings_data)}"
                )

            # Validate that all categories have embeddings
            missing_embeddings = [
                cat for cat in categories if cat not in embeddings_data
            ]
            if missing_embeddings:
                from ...core.exceptions import InvalidModelMetadataError

                raise InvalidModelMetadataError(
                    f"Missing embeddings for categories: {missing_embeddings}. "
                    f"All categories must have corresponding embeddings."
                )

            # Convert lists back to numpy arrays
            self.category_embeddings = {}
            for category, embedding_list in embeddings_data.items():
                if category in categories:
                    if not isinstance(embedding_list, list) or len(embedding_list) == 0:
                        from ...core.exceptions import InvalidModelMetadataError

                        raise InvalidModelMetadataError(
                            f"Invalid embedding for category '{category}'. "
                            f"Expected non-empty list, got: {type(embedding_list)}"
                        )
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

    def classify(self, text: str, filename: str = None) -> DocumentClassificationResult:
        """
        Classify text using pre-trained embeddings.

        Args:
            text: Input text to classify
            filename: Optional filename for context

        Returns:
            DocumentClassificationResult: Classification result
        """
        if not self.is_initialized or self.model is None:
            return DocumentClassificationResult(
                category="unknown",
                confidence=0.0,
                method="similarity",
                details={"error": "Classifier not initialized"},
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

    def retrain_with_corrections(
        self, corrections: List["CorrectionData"], model_path: str
    ) -> bool:
        """
        Retrain the similarity classifier with user corrections.
        Uses incremental model update approach.

        Args:
            corrections: List of CorrectionData objects with document details
            model_path: Path to save the updated model

        Returns:
            bool: True if retraining successful, False otherwise
        """
        try:
            from ...utils.model_updater import update_model_embeddings_incremental

            logger.info(
                f"Retraining similarity classifier with {len(corrections)} corrections"
            )

            # Use the incremental model update helper
            success = update_model_embeddings_incremental(corrections, model_path)

            if success:
                logger.info("Similarity classifier retraining completed successfully")
                # Reload the updated model
                return self.load_model(model_path)
            else:
                logger.error("Similarity classifier retraining failed")
                return False

        except Exception as e:
            logger.error(f"Error retraining similarity classifier: {e}")
            return False

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "categories": self.get_supported_categories(),
            "is_initialized": self.is_initialized,
            "type": "PreTrainedSimilarityClassifier",
        }
