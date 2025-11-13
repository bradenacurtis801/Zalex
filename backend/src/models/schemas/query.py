from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str

class Entity(BaseModel):
    """Named entity extracted from document text."""
    text: str
    label: str  # Entity type (e.g., "PERSON", "LOC", "ORG")
    start: int  # Start character position in the text
    end: int  # End character position in the text
    confidence: Optional[float] = None  # Optional confidence score (0.0-1.0)

class SearchResult(BaseModel):
    text: str
    source: str
    page: int
    score: Optional[float] = None
    entities: Optional[List[Entity]] = None  # NER entities extracted from the document

class QueryResponse(BaseModel):
    results: List[SearchResult]
