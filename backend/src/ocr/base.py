"""
Base OCR engine interface and types.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional


class OCREngineType(Enum):
    """Available OCR engine types."""

    TESSERACT = "tesseract"
    EASYOCR = "easyocr"


class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    def __init__(self, languages: List[str] = None):
        """
        Initialize the OCR engine.

        Args:
            languages: List of language codes (e.g., ['eng', 'spa'])
        """
        self.languages = languages or ["eng"]
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the OCR engine. Called once before first use."""
        pass

    @abstractmethod
    def extract_text(self, image_path: str) -> str:
        """
        Extract text from an image file.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as string
        """
        pass

    @abstractmethod
    def extract_text_from_bytes(
        self, image_bytes: bytes, image_format: str = "png"
    ) -> str:
        """
        Extract text from image bytes.

        Args:
            image_bytes: Raw image data
            image_format: Image format (png, jpg, etc.)

        Returns:
            Extracted text as string
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of supported language codes
        """
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if the engine is initialized."""
        return self._initialized

    def _ensure_initialized(self) -> None:
        """Ensure the engine is initialized before use."""
        if not self._initialized:
            self.initialize()
            self._initialized = True
