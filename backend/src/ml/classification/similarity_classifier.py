"""
Pre-trained similarity-based classifier for inference.
Uses SentenceTransformer embeddings with cosine similarity for classification.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from src.models.schemas.feedback import CorrectionData

from .base_classifier import DocumentClassifier, DocumentClassificationResult

logger = logging.getLogger(__name__)


class PreTrainedSimilarityClassifier(DocumentClassifier):
    """
    Pre-trained similarity-based classifier for inference only.
    Loads a trained model and provides classification functionality.
    Uses SentenceTransformer embeddings with cosine similarity.
    """

    def __init__(
        self,
        model_name_or_path: str,
        cache_folder: Optional[str] = None,
        token: Union[bool, str, None] = None,
    ):
        super().__init__(model_name_or_path, cache_folder, token)
        self.model: Optional[SentenceTransformer] = None
        self.category_embeddings: Dict[str, np.ndarray] = {}
        self.model_name: str = ""

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
        Load a pre-trained similarity classifier model.

        Args:
            model_dir: Path to the model directory. If None, uses self.model_name_or_path.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if model_dir is None:
                model_dir = self.model_name_or_path

            model_path = Path(model_dir)
            if not model_path.exists():
                logger.error(f"Model directory not found: {model_path}")
                return False

            # Validate model directory
            if not self.validate_model_directory(str(model_path)):
                logger.error(f"Invalid model directory: {model_path}")
                return False

            # Load model metadata
            metadata_file = model_path / "model_metadata.json"
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            self.model_name = metadata.get("model_name", "unknown")
            logger.info(f"Loading similarity classifier: {self.model_name}")

            # Load SentenceTransformer model
            sentence_transformer_path = model_path / "sentence_transformer"
            if sentence_transformer_path.exists():
                # Load from local directory
                self.model = SentenceTransformer(str(sentence_transformer_path))
                logger.info("Loaded SentenceTransformer from local directory")
            else:
                # Fallback to default model
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Using default SentenceTransformer model")

            # Load category embeddings
            embeddings_file = model_path / "category_embeddings.json"
            with open(embeddings_file, "r", encoding="utf-8") as f:
                embeddings_data = json.load(f)

            # Convert embeddings to numpy arrays
            for category, embedding_list in embeddings_data.items():
                self.category_embeddings[category] = np.array(embedding_list)

            logger.info(f"Loaded embeddings for {len(self.category_embeddings)} categories")
            logger.info(f"Categories: {list(self.category_embeddings.keys())}")

            self.is_initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to load similarity classifier: {e}")
            self.is_initialized = False
            return False

    def get_classifier_info(self) -> Dict[str, Any]:
        """Get information about the loaded classifier."""
        if not self.is_initialized:
            return {"error": "Classifier not initialized"}

        return {
            "type": "similarity",
            "model_name": self.model_name,
            "categories": list(self.category_embeddings.keys()),
            "num_categories": len(self.category_embeddings),
            "model_path": self.model_name_or_path,
        }

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

    def retrain_with_feedback(
        self, corrections: List["CorrectionData"], model_path: Optional[str] = None
    ) -> bool:
        """
        Retrain the similarity classifier with user feedback.

        Args:
            corrections: List of correction data from user feedback
            model_path: Optional path to save the updated model

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
                if model_path:
                    return self.load_model(model_path)
                return True
            else:
                logger.error("Similarity classifier retraining failed")
                return False

        except Exception as e:
            logger.error(f"Error during similarity classifier retraining: {e}")
            return False
