from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DocumentEntry(BaseModel):
    id: str  # Document ID (file hash)
    filename: str
    category: str
    confidence: float
    timestamp: str
    file_size: int
    mime_type: str
    status: str


class CategoryResponse(BaseModel):
    category: str
    documents: List[DocumentEntry]
    total_count: int


class CategoryDocument(BaseModel):
    """Document data within a category"""
    id: str  # Document ID (file hash)
    filename: str
    category: str
    confidence: float
    timestamp: str
    file_size: int
    mime_type: str
    status: str

class CategoriesResponse(BaseModel):
    categories: Dict[str, Dict[str, CategoryDocument]]  # category_name -> {filename -> CategoryDocument}
    total_documents: int


class DocumentFeedbackRequest(BaseModel):
    id: str  # Document ID (file hash)
    feedback_type: str  # "correct", "incorrect", "uncertain"
    suggested_category: Optional[str] = None
    comment: Optional[str] = None


class DocumentFeedbackResponse(BaseModel):
    message: str
    feedback_id: int
