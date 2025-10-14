from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DocumentEntry(BaseModel):
    filename: str
    file_path: str
    category: str
    confidence: float
    timestamp: str


class CategoryResponse(BaseModel):
    category: str
    documents: List[DocumentEntry]
    total_count: int


class CategoriesResponse(BaseModel):
    categories: Dict[
        str, Dict[str, Any]
    ]  # category_name -> {filename -> document_data}
    total_documents: int
