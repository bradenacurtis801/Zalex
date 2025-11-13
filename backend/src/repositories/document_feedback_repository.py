"""Repository for DocumentFeedback database operations."""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from sqlmodel import Session, select

from src.models.database import DocumentFeedback

logger = logging.getLogger(__name__)


class DocumentFeedbackRepository:
    """Repository for DocumentFeedback database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    def create(
        self,
        document_id: str,
        feedback_type: str,
        suggested_category: Optional[str] = None,
        comment: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> DocumentFeedback:
        """
        Create a new DocumentFeedback record.

        Args:
            document_id: Document ID (SHA256 hash)
            feedback_type: Type of feedback (e.g., "incorrect", "correct", "uncertain")
            suggested_category: Suggested category (optional)
            comment: User comment (optional)
            user_id: User ID who provided the feedback (optional)

        Returns:
            Created DocumentFeedback record
        """
        feedback = DocumentFeedback(
            document_id=document_id,
            feedback_type=feedback_type,
            suggested_category=suggested_category,
            comment=comment,
            user_id=user_id,
        )
        self._db.add(feedback)
        self._db.commit()
        self._db.refresh(feedback)
        return feedback

    def get_by_document_id(self, document_id: str) -> List[DocumentFeedback]:
        """
        Get all feedback records for a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            List of DocumentFeedback records
        """
        stmt = (
            select(DocumentFeedback)
            .where(DocumentFeedback.document_id == document_id)
            .order_by(DocumentFeedback.created_at.desc())
        )
        return list(self._db.exec(stmt).all())

    def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[DocumentFeedback]:
        """
        Get all feedback records with pagination.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)

        Returns:
            List of DocumentFeedback records
        """
        stmt = (
            select(DocumentFeedback)
            .offset(skip)
            .limit(limit)
            .order_by(DocumentFeedback.created_at.desc())
        )
        return list(self._db.exec(stmt).all())

    def get_total_count(self) -> int:
        """
        Get total count of all feedback records.

        Returns:
            Total number of feedback records
        """
        stmt = select(DocumentFeedback.id)
        return len(list(self._db.exec(stmt).all()))

    def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all feedback records for a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Number of records deleted
        """
        stmt = select(DocumentFeedback).where(DocumentFeedback.document_id == document_id)
        feedback_list = list(self._db.exec(stmt).all())

        for feedback in feedback_list:
            self._db.delete(feedback)

        self._db.commit()
        return len(feedback_list)

