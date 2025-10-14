"""Feedback router for handling user corrections and model updates."""

import logging

from fastapi import APIRouter, Depends
from src.dependencies import get_feedback_service
from src.models.feedback import (
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
) -> ReclassificationResponse:
    """
    Reclassify a document based on user feedback.

    Args:
        request: Reclassification request with document details
        feedback_service: Feedback service instance

    Returns:
        ReclassificationResponse with processing results
    """
    logger.info(f"Received reclassification request for {request.filename}")

    response = feedback_service.process_reclassification(request)
    logger.info(f"Reclassification completed: {response.success}")
    return response


@router.get("/feedback/summary", response_model=FeedbackSummary)
async def get_feedback_summary(
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackSummary:
    """
    Get a summary of feedback corrections and model updates.

    Args:
        feedback_service: Feedback service instance

    Returns:
        FeedbackSummary with correction statistics
    """
    logger.info("Received request for feedback summary")

    summary = feedback_service.get_feedback_summary()
    logger.info(f"Feedback summary: {summary.total_corrections} total corrections")
    return summary


@router.post("/feedback/update-model")
async def trigger_model_update(
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> dict:
    """
    Manually trigger a model update based on accumulated feedback.

    Args:
        feedback_service: Feedback service instance

    Returns:
        dict: Update status and results
    """
    logger.info("Received request to trigger model update")

    # Force a model update
    model_updated = feedback_service._update_model_embeddings()

    if model_updated:
        return {
            "success": True,
            "message": "Model updated successfully",
            "timestamp": feedback_service.feedback_data["last_updated"],
        }
    else:
        return {
            "success": False,
            "message": "Model update failed or no updates needed",
        }
