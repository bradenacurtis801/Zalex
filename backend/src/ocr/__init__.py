# OCR module exports
from .base import OCREngine, OCREngineType
from .easyocr_engine import EasyOCREngine
from .factory import create_ocr_engine
from .tesseract_engine import TesseractEngine

__all__ = [
    "OCREngine",
    "OCREngineType",
    "TesseractEngine",
    "EasyOCREngine",
    "create_ocr_engine",
]
