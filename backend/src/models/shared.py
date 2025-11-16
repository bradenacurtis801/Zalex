"""
Shared data structures for document processing.

These are intermediate data structures used during processing,
not database models or API schemas.
"""

from dataclasses import dataclass
from typing import Optional

from scanpro_lib.ocr.base import OCRResult


@dataclass
class OCRPage:
    """
    Intermediate data structure for a page with OCR results.
    Used during processing before persisting to database.
    
    This wraps OCRResult (from OCR engine) with page metadata.
    """
    page_number: int
    text: str
    ocr_result: OCRResult  # Raw OCR output from engine
    image_width: Optional[int] = None
    image_height: Optional[int] = None


@dataclass
class ProcessingTask:
    """In-memory representation of a document processing task."""
    document_id: str
    filename: str
    file_content: bytes
    user_id: Optional[int] = None
    db_task_id: Optional[int] = None  # ID of the database record

