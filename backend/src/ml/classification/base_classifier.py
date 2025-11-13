"""
Base document classifier interface and abstract classes.
Provides a generic interface for different classification strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from src.models.schemas.feedback import CorrectionData

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


class DocumentClassifier(ABC):
    """
    Abstract base class for document classifiers.
    Provides a common interface for different classification strategies.
    """

    def __init__(self, model_name_or_path: str, 
                cache_folder: Optional[str] = None,
                token: Union[bool, str, None] = None
                ):
        self.model_name_or_path = model_name_or_path
        self.cache_folder = cache_folder
        self.is_initialized = False

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

    def classify_document(
        self, 
        page_texts: List[Tuple[str, int]], 
        filename: str = None
    ) -> Tuple[str, float, int, Dict[str, Any]]:
        """
        Classify a multi-page document using classifier-specific strategy.
        This method handles the processing logic (chunking, aggregation, etc.)
        that varies by classifier type.
        
        Args:
            page_texts: List of tuples (text, page_number) for each page
            filename: Optional filename for context
            
        Returns:
            Tuple of (category, confidence, page_number, details_dict)
            - category: Predicted category name
            - confidence: Confidence score (0.0-1.0)
            - page_number: Page number that contributed to the classification (0-indexed)
            - details: Additional classification details
        """
        # Default implementation: aggregate all pages and classify
        # Subclasses can override for different strategies
        if not page_texts:
            return ("other", 0.0, 0, {})
        
        # Aggregate all pages with newline separator (matching training format)
        aggregated_text = "\n".join([text for text, _ in page_texts])
        
        if not aggregated_text or not aggregated_text.strip():
            return ("other", 0.0, 0, {})
        
        # Classify the aggregated text
        result = self.classify(aggregated_text, filename)
        
        # Return first page number as reference
        first_page_num = page_texts[0][1] if page_texts else 0
        
        return (
            result.category,
            result.confidence,
            first_page_num,
            result.details
        )

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
            "name": self.model_name_or_path,
            "is_initialized": self.is_initialized,
            "supported_categories": self.get_supported_categories(),
            "type": self.__class__.__name__,
        }
