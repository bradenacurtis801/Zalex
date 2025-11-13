"""Repository for DocumentClassification database operations."""

import logging
from typing import List, Optional
from datetime import datetime

from sqlmodel import Session, select
from typing import Tuple, List as ListType

from src.models.database import DocumentClassification, Document, User

logger = logging.getLogger(__name__)


class DocumentClassificationRepository:
    """Repository for DocumentClassification database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    def create(
        self,
        document_id: str,
        category: str,
        confidence: float,
        user_id: Optional[int] = None,
    ) -> DocumentClassification:
        """
        Create a new DocumentClassification record.

        Args:
            document_id: Document ID (SHA256 hash)
            category: Classification category
            confidence: Confidence score (0-1)
            user_id: User ID who created the classification (optional)

        Returns:
            Created DocumentClassification record
        """
        classification = DocumentClassification(
            document_id=document_id,
            category=category,
            confidence=confidence,
            user_id=user_id,
        )
        self._db.add(classification)
        self._db.commit()
        self._db.refresh(classification)
        return classification

    def get_by_document_id(
        self, document_id: str
    ) -> List[DocumentClassification]:
        """
        Get all classifications for a document, ordered by creation date (newest first).

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            List of DocumentClassification records
        """
        stmt = (
            select(DocumentClassification)
            .where(DocumentClassification.document_id == document_id)
            .order_by(DocumentClassification.created_at.desc())
        )
        return list(self._db.exec(stmt).all())

    def get_latest_by_document_id(
        self, document_id: str
    ) -> Optional[DocumentClassification]:
        """
        Get the latest classification for a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Latest DocumentClassification record if found, None otherwise
        """
        stmt = (
            select(DocumentClassification)
            .where(DocumentClassification.document_id == document_id)
            .order_by(DocumentClassification.created_at.desc())
            .limit(1)
        )
        return self._db.exec(stmt).first()

    def get_by_document_and_category(
        self, document_id: str, category: str
    ) -> Optional[DocumentClassification]:
        """
        Get classification for a document with a specific category.

        Args:
            document_id: Document ID (SHA256 hash)
            category: Category name

        Returns:
            DocumentClassification record if found, None otherwise
        """
        stmt = select(DocumentClassification).where(
            DocumentClassification.document_id == document_id,
            DocumentClassification.category == category,
        )
        return self._db.exec(stmt).first()

    def update(
        self,
        classification: DocumentClassification,
        category: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> DocumentClassification:
        """
        Update a classification record.

        Args:
            classification: Classification record to update
            category: New category (optional)
            confidence: New confidence score (optional)

        Returns:
            Updated DocumentClassification record
        """
        if category is not None:
            classification.category = category
        if confidence is not None:
            classification.confidence = confidence
        classification.updated_at = datetime.now()

        self._db.add(classification)
        self._db.commit()
        self._db.refresh(classification)
        return classification

    def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all classifications for a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Number of records deleted
        """
        stmt = select(DocumentClassification).where(
            DocumentClassification.document_id == document_id
        )
        classifications = list(self._db.exec(stmt).all())

        for classification in classifications:
            self._db.delete(classification)

        self._db.commit()
        return len(classifications)

    def get_all_categories(self) -> List[str]:
        """
        Get all unique categories from the database.

        Returns:
            List of unique category names
        """
        stmt = select(DocumentClassification.category).distinct()
        results = self._db.exec(stmt).all()

        categories = []
        for row in results:
            category = row[0] if isinstance(row, (tuple, list)) else row
            if category:
                categories.append(category)

        return sorted(list(set(categories)))

    def get_category_counts(self) -> dict[str, int]:
        """
        Get document counts per category.

        Returns:
            Dictionary mapping category names to document counts
        """
        stmt = select(
            DocumentClassification.category, DocumentClassification.id
        ).distinct()
        results = self._db.exec(stmt).all()

        summary = {}
        for category, _ in results:
            summary[category] = summary.get(category, 0) + 1

        return summary

    def get_documents_by_category(
        self, category: str, skip: int = 0, limit: int = 100
    ) -> ListType[Tuple[Document, DocumentClassification, Optional[User]]]:
        """
        Get documents in a specific category with their classifications and users.

        Args:
            category: Category name to filter by
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (for pagination)

        Returns:
            List of tuples (Document, DocumentClassification, Optional[User])
        """
        stmt = (
            select(Document, DocumentClassification, User)
            .join(
                DocumentClassification,
                Document.id == DocumentClassification.document_id,
            )
            .outerjoin(User, DocumentClassification.user_id == User.id)
            .where(DocumentClassification.category == category)
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.exec(stmt).all())

    def get_document_count_by_category(self, category: str) -> int:
        """
        Get total count of documents in a specific category.

        Args:
            category: Category name to filter by

        Returns:
            Total number of documents in the category
        """
        stmt = (
            select(Document.id)
            .join(
                DocumentClassification,
                Document.id == DocumentClassification.document_id,
            )
            .where(DocumentClassification.category == category)
        )
        return len(list(self._db.exec(stmt).all()))

    def get_all_documents_with_classifications(
        self, skip: int = 0, limit: int = 100
    ) -> ListType[Tuple[Document, DocumentClassification, Optional[User]]]:
        """
        Get all documents with their classifications and users (with pagination).

        Args:
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (for pagination)

        Returns:
            List of tuples (Document, DocumentClassification, Optional[User])
        """
        stmt = (
            select(Document, DocumentClassification, User)
            .join(
                DocumentClassification,
                Document.id == DocumentClassification.document_id,
            )
            .outerjoin(User, DocumentClassification.user_id == User.id)
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.exec(stmt).all())

    def get_total_document_count(self) -> int:
        """
        Get total count of all documents with classifications.

        Returns:
            Total number of documents with classifications
        """
        stmt = (
            select(Document.id)
            .join(
                DocumentClassification,
                Document.id == DocumentClassification.document_id,
            )
        )
        return len(list(self._db.exec(stmt).all()))

