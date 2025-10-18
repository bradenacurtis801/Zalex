from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DocumentClassification(BaseModel):
    filename: str
    category: str
    confidence: float


class DocumentInfo(BaseModel):
    id: str  # Document ID (file hash)
    filename: str
    file_size: int
    mime_type: str
    status: str
    created_at: datetime


class UploadResponse(BaseModel):
    message: str
    classifications: Optional[List[DocumentClassification]] = None
    already_classified: Optional[bool] = False
    document_info: Optional[DocumentInfo] = None


class PDFPagesRequest(BaseModel):
    document_id: str  # Document ID (file hash)
    max_pages: Optional[int] = 20


class PDFPagesResponse(BaseModel):
    filename: str
    total_pages: int
    pages: List[dict]  # List of page data with image_data, width, height, etc.
