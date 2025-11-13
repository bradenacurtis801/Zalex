"""Repository for UploadSessionFile database operations."""

import logging
from typing import List

from sqlmodel import Session, select

from src.models.database import UploadSessionFile

logger = logging.getLogger(__name__)


class UploadSessionFileRepository:
    """Repository for UploadSessionFile database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all UploadSessionFile records that reference a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Number of records deleted
        """
        stmt = select(UploadSessionFile).where(UploadSessionFile.document_id == document_id)
        session_files = list(self._db.exec(stmt).all())

        for session_file in session_files:
            self._db.delete(session_file)

        self._db.commit()
        return len(session_files)

