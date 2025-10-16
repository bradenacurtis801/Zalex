"""
Base document classifier interface and abstract classes.
Provides a generic interface for different classification strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from ...models.feedback import CorrectionData

logger = logging.getLogger(__name__)


class DocumentClassificationResult:
    """Result of document classification."""

    def __init__(
        self,
        category: str,
        confidence: float,
        method: str,
        details: Dict[str, Any] = None,
    ):
        self.category = category
        self.confidence = confidence
        self.method = method
        self.details = details or {}

    def __repr__(self):
        return f"DocumentClassificationResult(category='{self.category}', confidence={self.confidence:.3f}, method='{self.method}')"


class BaseDocumentClassifier(ABC):
    """
    Abstract base class for document classifiers.
    Provides a common interface for different classification strategies.
    """

    def __init__(self, name: str):
        self.name = name
        self.is_initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the classifier.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def classify(self, text: str, filename: str = None) -> DocumentClassificationResult:
        """
        Classify a document based on its text content.

        Args:
            text: The text content of the document to classify
            filename: Optional filename for context

        Returns:
            DocumentClassificationResult: Classification result
        """
        pass

    @abstractmethod
    def get_supported_categories(self) -> List[str]:
        """
        Get list of categories this classifier can predict.

        Returns:
            List[str]: List of supported category names
        """
        pass

    def build_category_embeddings(
        self, category_documents: Dict[str, List[str]]
    ) -> None:
        """
        Build embeddings for each category based on sample documents.
        Default implementation does nothing - subclasses can override.

        Args:
            category_documents: Dict mapping category names to lists of sample texts
        """
        logger.warning(
            f"build_category_embeddings not implemented for {self.__class__.__name__}"
        )
        pass

    def retrain_with_corrections(
        self, corrections: List["CorrectionData"], model_path: str
    ) -> bool:
        """
        Retrain the classifier with user corrections.
        Default implementation does nothing - subclasses must override.

        Args:
            corrections: List of CorrectionData objects with document details
            model_path: Path to save the updated model

        Returns:
            bool: True if retraining successful, False otherwise
        """
        logger.warning(
            f"retrain_with_corrections not implemented for {self.__class__.__name__}"
        )
        return False

    def get_classifier_info(self) -> Dict[str, Any]:
        """
        Get information about this classifier.

        Returns:
            Dict[str, Any]: Classifier information
        """
        return {
            "name": self.name,
            "is_initialized": self.is_initialized,
            "supported_categories": self.get_supported_categories(),
            "type": self.__class__.__name__,
        }
