"""
Base NER (Named Entity Recognition) interface and abstract classes.
Provides a generic interface for different NER strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from cv2 import normalize

logger = logging.getLogger(__name__)


class Entity:
    """Represents a named entity extracted from text."""

    def __init__(
        self,
        text: str,
        label: str,
        start: int,
        end: int,
        page_number: Optional[int] = None,
        normalized: Optional[str] = None,
        confidence: Optional[float] = None,
    ):
        """
        Initialize an entity.

        Args:
            text: The entity text
            label: The entity label/type (e.g., "PERSON", "LOCATION", "ORGANIZATION")
            start: Start character position in the text
            end: End character position in the text
            confidence: Optional confidence score (0.0-1.0)
        """
        self.text = text
        self.label = label
        self.start = start
        self.end = end
        self.page_number = page_number
        self.normalized = normalized
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "text": self.text,
            "label": self.label,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }

    def __repr__(self):
        return f"Entity(text='{self.text}', label='{self.label}', start={self.start}, end={self.end}, confidence={self.confidence})"


class NERResult:
    """Result of NER extraction."""

    def __init__(
        self,
        entities: List[Entity],
        method: str,
        details: Dict[str, Any] = None,
    ):
        """
        Initialize NER result.

        Args:
            entities: List of extracted entities
            method: Method/model used for extraction
            details: Additional details about the extraction
        """
        self.entities = entities
        self.method = method
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "entities": [entity.to_dict() for entity in self.entities],
            "method": self.method,
            "details": self.details,
        }

    def __repr__(self):
        return f"NERResult(entities={len(self.entities)}, method='{self.method}')"


class NERModel(ABC):
    """
    Abstract base class for NER models.
    Provides a common interface for different NER strategies.
    """

    def __init__(
        self,
        model_name_or_path: str,
        cache_folder: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize the NER model.

        Args:
            model_name_or_path: Model name or path (can be Hugging Face model ID or local path)
            cache_folder: Optional cache folder for model storage
            token: Optional token for private Hugging Face models
        """
        self.model_name_or_path = model_name_or_path
        self.cache_folder = cache_folder
        self.token = token
        self.is_initialized = False

    @abstractmethod
    def extract_entities(
        self, text: str, doc_type: Optional[str] = None
    ) -> NERResult:
        """
        Extract named entities from text.

        Args:
            text: The text to extract entities from
            doc_type: Optional document type/category (can be used to select model or adjust behavior)

        Returns:
            NERResult: Result containing extracted entities
        """
        pass

    @abstractmethod
    def get_supported_entity_types(self) -> List[str]:
        """
        Get list of entity types this model can extract.

        Returns:
            List[str]: List of supported entity type labels (e.g., ["PERSON", "LOCATION", "ORGANIZATION"])
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the model (load from disk, download, etc.).

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about this NER model.

        Returns:
            Dict[str, Any]: Model information
        """
        return {
            "name": self.model_name_or_path,
            "is_initialized": self.is_initialized,
            "supported_entity_types": self.get_supported_entity_types(),
            "type": self.__class__.__name__,
        }

