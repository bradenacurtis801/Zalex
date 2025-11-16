"""Repository for DocumentClassification database operations."""

import logging
from typing import List, Optional
from datetime import datetime

from sqlmodel import Session, select
from typing import Tuple, List as ListType
from sqlalchemy.dialects.postgresql import insert

from src.models.database import DocumentClassification, Document, User

logger = logging.getLogger(__name__)


class DocumentClassificationRepository:
    """Repository for DocumentClassification database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    def create_or_update(
        self,
        document_id: str,
        category: str,
        confidence: float,
        user_id: Optional[int] = None,
    ) -> DocumentClassification:
        """
        Create or update a DocumentClassification record using PostgreSQL UPSERT.
        This is atomic and handles race conditions efficiently.

        Args:
            document_id: Document ID (SHA256 hash)
            category: Classification category
            confidence: Confidence score (0-1)
            user_id: User ID who created/updated the classification (optional)

        Returns:
            Created or updated DocumentClassification record
        """
        # Build the insert statement
        stmt = insert(DocumentClassification).values(
            document_id=document_id,
            category=category,
            confidence=confidence,
            user_id=user_id,
        )
        
        # Build update dictionary for ON CONFLICT
        update_dict = {
            'category': stmt.excluded.category,
            'confidence': stmt.excluded.confidence,
        }
        if user_id is not None:
            update_dict['user_id'] = stmt.excluded.user_id
        
        # Use PostgreSQL's ON CONFLICT DO UPDATE (UPSERT)
        stmt = stmt.on_conflict_do_update(
            index_elements=['document_id'],
            set_=update_dict
        )
        
        # Execute the upsert
        self._db.execute(stmt)
        self._db.commit()
        
        # Fetch and return the updated/created record
        return self.get_by_document_id(document_id)

    def get_by_document_id(
        self, document_id: str
    ) -> Optional[DocumentClassification]:
        """
        Get the classification for a document (one-to-one relationship).

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            DocumentClassification record if found, None otherwise
        """
        stmt = select(DocumentClassification).where(
            DocumentClassification.document_id == document_id
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

    def delete_by_document_id(self, document_id: str) -> bool:
        """
        Delete the classification for a document (one-to-one relationship).

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            True if classification was deleted, False if not found
        """
        classification = self.get_by_document_id(document_id)
        if classification:
            self._db.delete(classification)
            self._db.commit()
            return True
        return False

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

