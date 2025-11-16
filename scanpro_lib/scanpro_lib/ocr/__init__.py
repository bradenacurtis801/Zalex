# OCR module exports
from .base import OCREngine, OCREngineType
from .easyocr_engine import EasyOCREngine
from .factory import create_ocr_engine
from .tesseract_engine import TesseractEngine
from .factory import get_default_ocr_engine

__all__ = [
    "OCREngine",
    "OCREngineType",
    "TesseractEngine",
    "EasyOCREngine",
    "create_ocr_engine",
    "get_default_ocr_engine",
]
