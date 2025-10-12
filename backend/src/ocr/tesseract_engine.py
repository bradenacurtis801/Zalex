"""
Tesseract OCR engine implementation.
"""

import logging
import os
import tempfile
from typing import List

import pytesseract
from pytesseract import TesseractNotFoundError
from PIL import Image

from .base import OCREngine

logger = logging.getLogger(__name__)


class TesseractEngine(OCREngine):
    """Tesseract OCR engine implementation."""

    def __init__(self, languages: List[str] = None):
        super().__init__(languages)
        self._tesseract_config = None

    def initialize(self) -> None:
        """Initialize Tesseract OCR engine."""
        logger.info("Initializing Tesseract OCR engine...")

        # Set up Tesseract configuration
        lang_string = "+".join(self.languages)
        self._tesseract_config = f"--oem 3 --psm 6 -l {lang_string}"

        # Test Tesseract availability
        try:
            pytesseract.get_tesseract_version()
            logger.info(
                f"Tesseract OCR initialized successfully with languages: {lang_string}"
            )
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            raise

    def extract_text(self, image_path: str) -> str:
        """Extract text from an image file using Tesseract."""
        self._ensure_initialized()

        try:
            logger.debug(f"Extracting text from {image_path} using Tesseract")
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img, config=self._tesseract_config)
            logger.debug(f"Successfully extracted {len(text)} characters")
            return text.strip()
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Tesseract OCR extraction failed: {e}")
            raise

    def extract_text_from_bytes(
        self, image_bytes: bytes, image_format: str = "png"
    ) -> str:
        """Extract text from image bytes using Tesseract."""
        self._ensure_initialized()

        try:
            # Create temporary file for Tesseract
            with tempfile.NamedTemporaryFile(
                suffix=f".{image_format}", delete=False
            ) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            # Extract text
            text = self.extract_text(temp_path)

            # Clean up temp file
            os.unlink(temp_path)

            return text
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Tesseract OCR extraction from bytes failed: {e}")
            raise

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes for Tesseract."""
        try:
            # Get available languages from Tesseract
            available_langs = pytesseract.get_languages()
            logger.debug(f"Tesseract available languages: {available_langs}")
            return available_langs
        except TesseractNotFoundError as e:
            logger.warning(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.warning(f"Could not get Tesseract languages: {e}")
            raise
