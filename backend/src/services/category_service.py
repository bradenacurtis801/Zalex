"""Category service for managing document categories and retrieval."""

import logging
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select

from src.ml.classification.base_classifier import BaseDocumentClassifier
from src.models.schemas.category import CategoriesResponse, CategoryResponse, DocumentEntry, CategoryDocument, UserInfo
from src.models.database import Document, DocumentClassification, User

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for handling document category operations."""

    def __init__(
        self, document_classifier: BaseDocumentClassifier, category_metadata: dict, db: Session
    ):
        self.document_classifier = document_classifier
        self.category_metadata = category_metadata
        self.db = db
        self._model_categories = None

    def _get_model_categories(self) -> List[str]:
        """
        Get categories from the trained model metadata.

        Returns:
            List of categories supported by the current model
        """
        if self._model_categories is not None:
            return self._model_categories

        try:
            # Get categories directly from the loaded classifier
            if self.document_classifier and self.document_classifier.is_initialized:
                self._model_categories = (
                    self.document_classifier.get_supported_categories()
                )
                logger.info(f"Loaded categories from model: {self._model_categories}")
                return self._model_categories
            else:
                logger.warning("Document classifier not available")
        except Exception as e:
            logger.warning(f"Failed to load model categories: {e}")

        # No fallback - backend requires a trained model
        logger.error("Cannot get categories without a trained model")
        return []

    def get_documents_by_category(self, category: str, skip: int = 0, limit: int = 100) -> CategoryResponse:
        """
        Get all documents in a specific category.

        Args:
            category: The category name to filter by
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (for pagination)

        Returns:
            CategoryResponse with documents in the category
        """
        logger.info(f"Retrieving documents for category: {category} (skip={skip}, limit={limit})")

        # First check if category exists in the model
        available_categories = self._get_model_categories()
        if category not in available_categories:
            logger.warning(f"Category '{category}' not found in model")
            return CategoryResponse(
                category=category,
                documents=[],
                total_count=0,
            )

        # Query database for documents in this category with users (with pagination)
        stmt = select(Document, DocumentClassification, User).join(
            DocumentClassification, Document.id == DocumentClassification.document_id
        ).outerjoin(User, DocumentClassification.user_id == User.id).where(DocumentClassification.category == category).offset(skip).limit(limit)
        
        results = self.db.exec(stmt).all()
        
        # Get total count for this category
        total_count_stmt = select(Document.id).join(
            DocumentClassification, Document.id == DocumentClassification.document_id
        ).where(DocumentClassification.category == category)
        total_count = len(self.db.exec(total_count_stmt).all())
        
        # Convert to DocumentEntry objects
        document_entries = []
        for document, classification, user in results:
            document_entries.append(
                DocumentEntry(
                    id=document.id,  # Document ID (file hash)
                    filename=document.filename,
                    category=classification.category,
                    confidence=classification.confidence,
                    timestamp=document.created_at.isoformat() if document.created_at else "",
                    file_size=document.file_size or 0,
                    mime_type=document.mime_type or "application/octet-stream",
                    status=document.status.value if document.status else "unknown",
                )
            )

        logger.info(f"Found {len(document_entries)} documents in category '{category}' (total: {total_count})")

        return CategoryResponse(
            category=category,
            documents=document_entries,
            total_count=total_count,
        )

    def get_all_categories(self, skip: int = 0, limit: int = 100) -> CategoriesResponse:
        """
        Get all available categories and their document counts.

        Args:
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (for pagination)

        Returns:
            CategoriesResponse with all categories and their documents
        """
        logger.info(f"Retrieving all categories (skip={skip}, limit={limit})")

        # Get categories from model
        available_categories = self._get_model_categories()

        # Query database for documents with their classifications and users (with pagination)
        stmt = select(Document, DocumentClassification, User).join(
            DocumentClassification, Document.id == DocumentClassification.document_id
        ).outerjoin(User, DocumentClassification.user_id == User.id).offset(skip).limit(limit)
        
        results = self.db.exec(stmt).all()
        
        # Group documents by category
        categories_data = {}
        for document, classification, user in results:
            category = classification.category
            if category not in categories_data:
                categories_data[category] = {}
            
            # Prepare user data
            user_data = None
            if user:
                user_data = UserInfo(
                    username=user.username,
                    full_name=user.full_name
                )
            
            # Convert to CategoryDocument model
            categories_data[category][document.filename] = CategoryDocument(
                id=document.id,  # Document ID (file hash)
                filename=document.filename,
                category=classification.category,
                confidence=classification.confidence,
                timestamp=document.created_at.isoformat() if document.created_at else "",
                file_size=document.file_size or 0,
                mime_type=document.mime_type or "application/octet-stream",
                status=document.status.value if document.status else "unknown",
                user=user_data
            )

        # Get total count for pagination info
        total_count_stmt = select(Document.id).join(
            DocumentClassification, Document.id == DocumentClassification.document_id
        )
        total_documents = len(self.db.exec(total_count_stmt).all())

        logger.info(
            f"Found {len(categories_data)} categories with {len(results)} documents (total: {total_documents})"
        )

        return CategoriesResponse(
            categories=categories_data, total_documents=total_documents
        )

    def get_categories_summary(self) -> Dict[str, int]:
        """
        Get a summary of document counts per category.

        Returns:
            Dictionary mapping category names to document counts
        """
        logger.info("Retrieving categories summary")

        # Query database for document counts per category
        stmt = select(DocumentClassification.category, DocumentClassification.id).distinct()
        results = self.db.exec(stmt).all()
        
        # Count documents per category
        summary = {}
        for category, _ in results:
            summary[category] = summary.get(category, 0) + 1

        logger.info(f"Categories summary: {summary}")

        return summary
