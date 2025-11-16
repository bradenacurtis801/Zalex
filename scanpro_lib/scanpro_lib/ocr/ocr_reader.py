"""
Legacy OCR reader interface for backward compatibility.
This module provides the old interface while using the new OCR engine system.
"""

import logging
from typing import List

from .base import OCREngine
from .factory import get_default_ocr_engine
from pytesseract import TesseractNotFoundError
from src.core.exceptions import OCRNotAvailableException, DocumentProcessingException

logger = logging.getLogger(__name__)

# Global OCR engine instance
_ocr_engine: OCREngine = None


def get_ocr_reader():
    """
    Get the OCR reader instance (legacy interface).

    Returns:
        OCR engine instance
    """
    global _ocr_engine
    if _ocr_engine is None:
        logger.info("Initializing OCR engine...")
        _ocr_engine = get_default_ocr_engine()
    return _ocr_engine


def extract_text_from_image(image_path: str, languages: str = "eng+spa") -> str:
    """
    Extract text from an image using the configured OCR engine.

    Args:
        image_path: Path to the image file
        languages: Language codes for OCR (default: 'eng+spa' for English and Spanish)

    Returns:
        Extracted text as string
        
    Raises:
        OCRNotAvailableException: If Tesseract OCR is not available
        DocumentProcessingException: If document processing fails
    """
    try:
        engine = get_ocr_reader()

        # Convert language string to list
        lang_list = [lang.strip() for lang in languages.split("+")]

        # Create a new engine instance with the specified languages if different
        if set(lang_list) != set(engine.languages):
            from .factory import create_ocr_engine

            engine = create_ocr_engine(languages=lang_list)

        ocr_result = engine.extract_text(image_path)
        return ocr_result.text
    except TesseractNotFoundError as e:
        raise OCRNotAvailableException(f"Tesseract OCR is not available: {str(e)}")
    except Exception as e:
        raise DocumentProcessingException(f"OCR extraction failed: {str(e)}")


def extract_text_from_bytes(
    image_bytes: bytes, image_format: str = "png", languages: str = "eng+spa"
) -> str:
    """
    Extract text from image bytes using the configured OCR engine.

    Args:
        image_bytes: Raw image data
        image_format: Image format (png, jpg, etc.)
        languages: Language codes for OCR (default: 'eng+spa' for English and Spanish)

    Returns:
        Extracted text as string
        
    Raises:
        OCRNotAvailableException: If Tesseract OCR is not available
        DocumentProcessingException: If document processing fails
    """
    try:
        engine = get_ocr_reader()

        # Convert language string to list
        lang_list = [lang.strip() for lang in languages.split("+")]

        # Create a new engine instance with the specified languages if different
        if set(lang_list) != set(engine.languages):
            from .factory import create_ocr_engine

            engine = create_ocr_engine(languages=lang_list)

        ocr_result = engine.extract_text_from_bytes(image_bytes, image_format)
        return ocr_result.text
    except TesseractNotFoundError as e:
        raise OCRNotAvailableException(f"Tesseract OCR is not available: {str(e)}")
    except Exception as e:
        raise DocumentProcessingException(f"OCR extraction failed: {str(e)}")
