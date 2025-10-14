from datetime import datetime
from typing import List, Optional

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
    categories: dict
    total_documents: int
