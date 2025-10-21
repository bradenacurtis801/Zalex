"""
OCR data API response schemas.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class OCRWordData(BaseModel):
    """Word-level OCR data with bounding box information."""
    text: str
    confidence: int
    bbox: Dict[str, int]  # {"left": int, "top": int, "width": int, "height": int}
    block_num: int
    par_num: int
    line_num: int
    word_num: int


class OCRLineData(BaseModel):
    """Line-level OCR data with bounding box information."""
    text: str
    confidence: float
    bbox: Dict[str, int]  # {"left": int, "top": int, "width": int, "height": int}
    words: List[OCRWordData]
    block_num: int
    par_num: int
    line_num: int


class OCRDataResponse(BaseModel):
    """OCR data response for a single page."""
    id: int
    page_number: int
    full_text: str
    confidence_score: float
    total_words: int
    total_lines: int
    words_data: List[OCRWordData]
    lines_data: List[OCRLineData]
    original_image_width: Optional[int] = None
    original_image_height: Optional[int] = None
    created_at: datetime


class DocumentOCRDataResponse(BaseModel):
    """Response for getting all OCR data for a document."""
    document_id: str
    total_pages: int
    ocr_data: List[OCRDataResponse]


class PageOCRDataResponse(BaseModel):
    """Response for getting OCR data for a specific page."""
    id: int
    document_id: str
    page_number: int
    full_text: str
    confidence_score: float
    total_words: int
    total_lines: int
    words_data: List[OCRWordData]
    lines_data: List[OCRLineData]
    created_at: datetime


class OCRSearchMatch(BaseModel):
    """Search match result."""
    page_number: int
    position: int
    text: str
    confidence: float


class OCRSearchResponse(BaseModel):
    """Response for OCR text search."""
    document_id: str
    query: str
    case_sensitive: bool
    total_matches: int
    matches: List[OCRSearchMatch]


class DocumentTextSummary(BaseModel):
    """Document text summary."""
    total_pages: int
    total_words: int
    total_lines: int
    average_confidence: float
    full_text: str


class OCRSummaryResponse(BaseModel):
    """Response for document text summary."""
    document_id: str
    summary: DocumentTextSummary
