from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class EntityFilter(BaseModel):
    label: str
    text: str
    match: Optional[str] = "contains"


class QueryFilters(BaseModel):
    """Typed structured filters for the /query endpoint.

    date_from and date_to are parsed by Pydantic/FastAPI from ISO date strings
    (YYYY-MM-DD) into `datetime.date` objects.
    """
    date_from: Optional[date] = Field(None, description="Inclusive start date (YYYY-MM-DD)")
    date_to: Optional[date] = Field(None, description="Inclusive end date (YYYY-MM-DD)")
    entity_filter: Optional[List[EntityFilter]] = None
    category_filter: Optional[str] = None


class QueryRequest(BaseModel):
    query: str
    limit: Optional[int] = None  # Optional limit on number of results (defaults to service default)
    filters: Optional[QueryFilters] = None

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
