"""Feedback service for handling user corrections and model updates."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlmodel import Session, select

import config
import numpy as np
from sentence_transformers import SentenceTransformer
from src.core.exceptions import (
    CategoryNotFoundError,
    DocumentNotFoundError,
    FeedbackException,
)
from src.ml.classification.base_classifier import BaseDocumentClassifier
from src.models.schemas.feedback import (
    FeedbackSummary,
    ReclassificationRequest,
    ReclassificationResponse,
)
from src.models.database import Document, DocumentClassification

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for handling user feedback and model corrections."""

    def __init__(
        self,
        document_classifier: BaseDocumentClassifier,
        category_metadata: dict,
        db: Session,
    ):
        self.document_classifier = document_classifier
        self.category_metadata = category_metadata
        self.db = db


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

        # Log the correction
        self._log_correction(request, user_id)

        # Get updated categories
        updated_categories = self._get_available_categories()

        return ReclassificationResponse(
            success=True,
            message=f"Document reclassified from {request.current_category} to {request.new_category}",
            updated_categories=updated_categories,
        )

    def _get_available_categories(self) -> List[str]:
        """Get list of available categories from the model."""
        try:
            if self.document_classifier and self.document_classifier.is_initialized:
                return self.document_classifier.get_supported_categories()
            else:
                # Fallback to category metadata
                return list(self.category_metadata.keys())
        except Exception as e:
            logger.error(f"Error getting available categories: {e}")
            return ["other"]

    def _update_document_category(self, request: ReclassificationRequest):
        """Update the document's category in the database."""
        # Find the document by ID
        document = self.db.get(Document, request.id)
        
        if not document:
            raise DocumentNotFoundError(
                f"Document with ID '{request.id}' not found"
            )
        
        # Find the classification for this document
        stmt = select(DocumentClassification).where(
            DocumentClassification.document_id == request.id
        )
        classification = self.db.exec(stmt).first()
        
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
        classification.category = request.new_category
        if request.confidence is not None:
            classification.confidence = request.confidence
        
        # Update document timestamp
        document.updated_at = datetime.now()
        
        # Save changes to database
        self.db.add(classification)
        self.db.add(document)
        self.db.commit()
        
        logger.info(
            f"Document ID '{request.id}' reclassified from {request.current_category} to {request.new_category}"
        )

    def _log_correction(self, request: ReclassificationRequest, user_id: Optional[int] = None):
        """Log the correction in the database for tracking and model updates."""
        from src.models.database import DocumentFeedback
        
        # Create feedback record using the document ID directly
        feedback = DocumentFeedback(
            document_id=request.id,
            user_id=user_id,  # Track who made the update
            feedback_type="incorrect",  # Reclassification implies incorrect classification
            suggested_category=request.new_category,
            comment=request.user_comment,
        )
        
        self.db.add(feedback)
        self.db.commit()
        
        logger.info(f"Feedback logged for document ID '{request.id}' by user {user_id}")


    def get_feedback_summary(self, skip: int = 0, limit: int = 100) -> FeedbackSummary:
        """Get a summary of feedback corrections from database."""
        from src.models.database import DocumentFeedback
        
        # Get feedback records with pagination
        stmt = select(DocumentFeedback).offset(skip).limit(limit).order_by(DocumentFeedback.created_at.desc())
        feedback_records = self.db.exec(stmt).all()
        
        # Get total count for pagination info
        total_count_stmt = select(DocumentFeedback.id)
        total_corrections = len(self.db.exec(total_count_stmt).all())
        
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
