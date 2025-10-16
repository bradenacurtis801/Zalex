"""Category service for managing document categories and retrieval."""

import logging
import os
from typing import Any, Dict, List, Optional

from src.ml.classification.base_classifier import BaseDocumentClassifier
from src.models.category import CategoriesResponse, CategoryResponse, DocumentEntry

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for handling document category operations."""

    def __init__(
        self, document_classifier: BaseDocumentClassifier, category_metadata: dict
    ):
        self.document_classifier = document_classifier
        self.category_metadata = category_metadata
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

    def get_documents_by_category(self, category: str) -> CategoryResponse:
        """
        Get all documents in a specific category.

        Args:
            category: The category name to filter by

        Returns:
            CategoryResponse with documents in the category
        """
        logger.info(f"Retrieving documents for category: {category}")

        # First check if category exists in the model
        available_categories = self._get_model_categories()
        if category not in available_categories:
            logger.warning(f"Category '{category}' not found in directory structure")
            return CategoryResponse(
                category=category,
                documents=[],
                total_count=0,
            )

        # Get documents from category metadata
        category_metadata = self.category_metadata
        documents = category_metadata.get(category, {})

        # Convert to DocumentEntry objects
        document_entries = []
        for filename, doc in documents.items():
            document_entries.append(
                DocumentEntry(
                    filename=filename,
                    file_path=doc.get("file_path", ""),
                    category=doc.get("category", "other"),
                    confidence=doc.get("confidence", 0.0),
                    timestamp=doc.get("timestamp", ""),
                )
            )

        logger.info(f"Found {len(document_entries)} documents in category '{category}'")

        return CategoryResponse(
            category=category,
            documents=document_entries,
            total_count=len(document_entries),
        )

    def get_all_categories(self) -> CategoriesResponse:
        """
        Get all available categories and their document counts.

        Returns:
            CategoriesResponse with all categories and their documents
        """
        logger.info("Retrieving all categories")

        # Get categories from model
        available_categories = self._get_model_categories()

        # Get category summary from model metadata only
        category_summary = {}

        # Get metadata from injected dependency
        category_metadata = self.category_metadata

        # Merge model-based categories with category metadata
        merged_categories = {}
        for category in available_categories:
            if category in category_metadata:
                merged_categories[category] = category_metadata[category]
            else:
                # Create basic structure for categories found in model but not in metadata
                merged_categories[category] = {}

        total_documents = sum(
            len(docs) for docs in merged_categories.values() if isinstance(docs, dict)
        )

        logger.info(
            f"Found {len(available_categories)} categories with {total_documents} total documents"
        )

        return CategoriesResponse(
            categories=merged_categories, total_documents=total_documents
        )

    def get_categories_summary(self) -> Dict[str, int]:
        """
        Get a summary of document counts per category.

        Returns:
            Dictionary mapping category names to document counts
        """
        logger.info("Retrieving categories summary")

        # Get summary from model metadata only
        summary = {}

        logger.info(f"Categories summary: {summary}")

        return summary
