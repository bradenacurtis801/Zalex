"""Category service for managing document categories and retrieval."""

import logging
from typing import Any, Dict, List, Optional

from src.ml.classification.base_classifier import DocumentClassifier
from src.models.schemas.category import CategoriesResponse, CategoryResponse, DocumentEntry, CategoryDocument, UserInfo
from src.repositories.document_classification_repository import DocumentClassificationRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.document_repository import DocumentRepository
from src.models.database import DocumentStatus
from src.core.exceptions import CategoryAlreadyExistsError

from scanpro_lib.utils.file_hasher import calculate_file_hash_from_content

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for handling document category operations."""

    def __init__(
        self,
        document_classifier: DocumentClassifier,
        classification_repo: Optional[DocumentClassificationRepository],
    ):
        self.document_classifier = document_classifier
        self.classification_repo = classification_repo

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

        # Check if category exists in the database
        available_categories = self.classification_repo.get_all_categories()
        if category not in available_categories:
            logger.warning(f"Category '{category}' not found in database")
            return CategoryResponse(
                category=category,
                documents=[],
                total_count=0,
            )

        # Get documents from repository
        results = self.classification_repo.get_documents_by_category(category, skip, limit)
        total_count = self.classification_repo.get_document_count_by_category(category)
        
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

        # Get documents from repository
        results = self.classification_repo.get_all_documents_with_classifications(skip, limit)
        total_documents = self.classification_repo.get_total_document_count()
        
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

        summary = self.classification_repo.get_category_counts()

        logger.info(f"Categories summary: {summary}")
        return summary
