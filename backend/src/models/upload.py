from typing import List, Optional

from pydantic import BaseModel


class DocumentClassification(BaseModel):
    filename: str
    category: str
    confidence: float


class UploadResponse(BaseModel):
    message: str
    classifications: Optional[List[DocumentClassification]] = None
    already_classified: Optional[bool] = False
