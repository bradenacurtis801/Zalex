from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ReclassificationRequest(BaseModel):
    """Request model for document reclassification feedback."""

    filename: str
    current_category: str
    new_category: str
    confidence: Optional[float] = None
    user_comment: Optional[str] = None


class ReclassificationResponse(BaseModel):
    """Response model for reclassification feedback."""

    success: bool
    message: str
    updated_categories: Optional[List[str]] = None
    model_updated: bool = False


class FeedbackSummary(BaseModel):
    """Summary of feedback corrections."""

    total_corrections: int
    corrections_by_category: dict
    last_updated: datetime
    model_version: str
