from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    text: str
    source: str
    page: int
    score: Optional[float] = None

class QueryResponse(BaseModel):
    results: List[SearchResult]
