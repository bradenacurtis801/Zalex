"""Feedback router for handling user corrections and model updates."""

import logging

from fastapi import APIRouter, Depends
from src.dependencies import get_feedback_service, get_current_user
from src.models.database import User
from src.models.schemas.feedback import (
    FeedbackSummary,
    ReclassificationRequest,
    ReclassificationResponse,
)
from src.services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/feedback/reclassify", response_model=ReclassificationResponse)
async def reclassify_document(
    request: ReclassificationRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service),
    current_user: User = Depends(get_current_user),
) -> ReclassificationResponse:
    """
    Reclassify a document based on user feedback.

    Args:
        request: Reclassification request with document details
        feedback_service: Feedback service instance
        current_user: Authenticated user

    Returns:
        ReclassificationResponse with processing results
    """
    logger.info(f"Received reclassification request for {request.filename} from user {current_user.id}")
    return feedback_service.process_reclassification(request, current_user.id)


@router.get("/feedback/summary", response_model=FeedbackSummary)
async def get_feedback_summary(
    skip: int = 0,
    limit: int = 100,
    feedback_service: FeedbackService = Depends(get_feedback_service),
    current_user: User = Depends(get_current_user),
) -> FeedbackSummary:
    """
    Get a summary of feedback corrections and model updates.

    Args:
        skip: Number of feedback records to skip (for pagination)
        limit: Maximum number of feedback records to return (for pagination)
        feedback_service: Feedback service instance
        current_user: Authenticated user

    Returns:
        FeedbackSummary with correction statistics
    """
    logger.info(f"Received request for feedback summary from user {current_user.id} (skip={skip}, limit={limit})")
    return feedback_service.get_feedback_summary(skip=skip, limit=limit)