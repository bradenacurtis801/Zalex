"""
OCR engine factory for creating OCR instances.
"""

import logging
from typing import List

from .base import OCREngine, OCREngineType
from .easyocr_engine import EasyOCREngine
from .tesseract_engine import TesseractEngine

logger = logging.getLogger(__name__)


def create_ocr_engine(
    engine_type: OCREngineType = OCREngineType.TESSERACT,
    languages: List[str] = None,
) -> OCREngine:
    """
    Create an OCR engine instance.

    Args:
        engine_type: Type of OCR engine to create (default: TESSERACT)
        languages: List of language codes (e.g., ['eng', 'spa'])

    Returns:
        OCR engine instance
    """
    # Set default languages
    if languages is None:
        languages = ["eng", "spa"]  # English and Spanish by default

    # Create engine instance
    logger.info(f"Creating OCR engine: {engine_type.value} with languages: {languages}")

    if engine_type == OCREngineType.TESSERACT:
        return TesseractEngine(languages)
    elif engine_type == OCREngineType.EASYOCR:
        return EasyOCREngine(languages)
    else:
        raise ValueError(f"Unsupported OCR engine type: {engine_type}")


def get_default_ocr_engine() -> OCREngine:
    """
    Get the default OCR engine instance (Tesseract).

    Returns:
        Default OCR engine instance
    """
    return create_ocr_engine(OCREngineType.TESSERACT, languages=['spa'])
