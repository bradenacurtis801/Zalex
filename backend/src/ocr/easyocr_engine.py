"""
EasyOCR engine implementation.
"""

import logging
import os
import tempfile
from typing import List

import easyocr
from PIL import Image

from .base import OCREngine

logger = logging.getLogger(__name__)


class EasyOCREngine(OCREngine):
    """EasyOCR engine implementation."""

    def __init__(self, languages: List[str] = None):
        super().__init__(languages)
        self._reader = None

    def initialize(self) -> None:
        """Initialize EasyOCR engine."""
        logger.info("Initializing EasyOCR engine...")

        try:
            # Convert language codes to EasyOCR format
            easyocr_langs = []
            for lang in self.languages:
                if lang == "eng":
                    easyocr_langs.append("en")
                elif lang == "spa":
                    easyocr_langs.append("es")
                else:
                    # Map other languages as needed
                    easyocr_langs.append(lang)

            logger.debug(f"Creating EasyOCR reader with languages: {easyocr_langs}")
            self._reader = easyocr.Reader(easyocr_langs)
            logger.info("EasyOCR engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise

    def extract_text(self, image_path: str) -> str:
        """Extract text from an image file using EasyOCR."""
        self._ensure_initialized()

        try:
            logger.debug(f"Extracting text from {image_path} using EasyOCR")
            results = self._reader.readtext(image_path, detail=0, paragraph=True)

            # Join all text chunks
            text = "\n".join(results) if results else ""
            logger.debug(f"Successfully extracted {len(text)} characters")
            return text.strip()
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return ""

    def extract_text_from_bytes(
        self, image_bytes: bytes, image_format: str = "png"
    ) -> str:
        """Extract text from image bytes using EasyOCR."""
        self._ensure_initialized()

        try:
            # Create temporary file for EasyOCR
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
        except Exception as e:
            logger.error(f"EasyOCR extraction from bytes failed: {e}")
            return ""

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes for EasyOCR."""
        # EasyOCR supports many languages, return common ones
        return [
            "eng",
            "spa",
            "fra",
            "deu",
            "ita",
            "por",
            "rus",
            "jpn",
            "kor",
            "chi_sim",
            "chi_tra",
        ]
