"""Repository for Category database operations."""

import logging
from typing import List, Optional

from sqlmodel import Session, select

from src.models.database import Category, CategoryTrainingDocument, Document

logger = logging.getLogger(__name__)


class CategoryRepository:
    """Repository for Category database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    def get_by_name(self, name: str) -> Optional[Category]:
        """
        Get a category by name.

        Args:
            name: Category name

        Returns:
            Category if found, None otherwise
        """
        stmt = select(Category).where(Category.name == name)
        return self._db.exec(stmt).first()

    def get_by_id(self, category_id: int) -> Optional[Category]:
        """
        Get a category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category if found, None otherwise
        """
        return self._db.get(Category, category_id)

    def get_all(self) -> List[Category]:
        """
        Get all categories.

        Returns:
            List of all Category objects
        """
        stmt = select(Category).where(Category.is_active == True)
        return list(self._db.exec(stmt).all())

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Category:
        """
        Create a new category.

        Args:
            name: Category name
            description: Category description (optional)
            created_by: User ID who created the category (optional)

        Returns:
            Created Category record
        """
        category = Category(
            name=name,
            description=description,
            created_by=created_by,
        )
        self._db.add(category)
        self._db.commit()
        self._db.refresh(category)
        return category

    def add_training_document(
        self,
        category_id: int,
        document_id: str,
        uploaded_by: Optional[int] = None,
    ) -> CategoryTrainingDocument:
        """
        Add a training document to a category.

        Args:
            category_id: Category ID
            document_id: Document ID
            uploaded_by: User ID who uploaded the document (optional)

        Returns:
            Created CategoryTrainingDocument record
        """
        training_doc = CategoryTrainingDocument(
            category_id=category_id,
            document_id=document_id,
            uploaded_by=uploaded_by,
        )
        self._db.add(training_doc)
        self._db.commit()
        self._db.refresh(training_doc)
        return training_doc

    def get_training_documents(self, category_id: int) -> List[CategoryTrainingDocument]:
        """
        Get all training documents for a category.

        Args:
            category_id: Category ID

        Returns:
            List of CategoryTrainingDocument objects
        """
        stmt = select(CategoryTrainingDocument).where(
            CategoryTrainingDocument.category_id == category_id
        )
        return list(self._db.exec(stmt).all())

