"""Feedback service for handling user corrections and model updates."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlmodel import select

from src.core.exceptions import DocumentNotFoundError
from src.ml.classification.base_classifier import DocumentClassifier
from src.models.schemas.feedback import (
    FeedbackSummary,
    ReclassificationRequest,
    ReclassificationResponse,
)
from src.repositories.document_repository import DocumentRepository
from src.repositories.document_classification_repository import DocumentClassificationRepository
from src.repositories.document_feedback_repository import DocumentFeedbackRepository

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for handling user feedback and model corrections."""

    def __init__(
        self,
        document_classifier: DocumentClassifier,
        document_repo: DocumentRepository,
        classification_repo: DocumentClassificationRepository,
        feedback_repo: DocumentFeedbackRepository,
    ):
        self.document_classifier = document_classifier
        self.document_repo = document_repo
        self.classification_repo = classification_repo
        self.feedback_repo = feedback_repo


    def process_reclassification(
        self, request: ReclassificationRequest, user_id: Optional[int] = None
    ) -> ReclassificationResponse:
        """
        Process a document reclassification request.

        Args:
            request: Reclassification request with document details
            user_id: ID of the user making the reclassification

        Returns:
            ReclassificationResponse with processing results
        """
        logger.info(
            f"Processing reclassification: {request.filename} from {request.current_category} to {request.new_category}"
        )

        # Validate the new category
        available_categories = self._get_available_categories()
        if request.new_category not in available_categories:
            # If category doesn't exist, add it to 'other'
            request.new_category = "other"
            logger.info(
                f"Category '{request.new_category}' not found, using 'other'"
            )

        # Update the document in category metadata
        # This will throw an exception if it fails
        self._update_document_category(request)

        self.feedback_repo.create(
            document_id=request.id,
            user_id=user_id,
            feedback_type="incorrect",  # Reclassification implies incorrect classification
            suggested_category=request.new_category,
            comment=request.user_comment,
        )

        # Get updated categories
        updated_categories = self._get_available_categories()

        return ReclassificationResponse(
            success=True,
            message=f"Document reclassified from {request.current_category} to {request.new_category}",
            updated_categories=updated_categories,
        )

    def _update_document_category(self, request: ReclassificationRequest):
        """Update the document's category in the database."""
        # Find the document by ID
        document = self.document_repo.get_by_id(request.id)
        
        if not document:
            raise DocumentNotFoundError(
                f"Document with ID '{request.id}' not found"
            )
        
        # Find the classification for this document
        classifications = self.classification_repo.get_by_document_id(request.id)
        classification = classifications[0] if classifications else None
        
        if not classification:
            raise DocumentNotFoundError(
                f"No classification found for document ID '{request.id}'"
            )
        
        # Verify the current category matches
        if classification.category != request.current_category:
            raise DocumentNotFoundError(
                f"Document ID '{request.id}' is not in category '{request.current_category}'"
            )
        
        # Update the classification
        self.classification_repo.update(
            classification,
            category=request.new_category,
            confidence=request.confidence,
        )
        
        logger.info(
            f"Document ID '{request.id}' reclassified from {request.current_category} to {request.new_category}"
        )

    def _get_available_categories(self) -> List[str]:
        """Queries DB for available categories."""
        return self.classification_repo.get_all_categories()

    def get_feedback_summary(self, skip: int = 0, limit: int = 100) -> FeedbackSummary:
        """Get a summary of feedback corrections from database."""
        # Get feedback records with pagination
        feedback_records = self.feedback_repo.get_all(skip, limit)
        
        # Get total count for pagination info
        total_corrections = self.feedback_repo.get_total_count()
        
        # Count corrections by category
        corrections_by_category = {}
        for feedback in feedback_records:
            category = feedback.suggested_category or "unknown"
            corrections_by_category[category] = corrections_by_category.get(category, 0) + 1
        
        # Get latest feedback timestamp
        latest_feedback = max(feedback_records, key=lambda f: f.created_at) if feedback_records else None
        last_updated = latest_feedback.created_at if latest_feedback else datetime.now()
        
        return FeedbackSummary(
            total_corrections=total_corrections,
            corrections_by_category=corrections_by_category,
            last_updated=last_updated,
            model_version="1.0.0",  # Could be stored in database or config
        )
