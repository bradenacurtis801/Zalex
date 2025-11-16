"""Repository for Document data access operations."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from sqlmodel import Session, select

from src.models.database import (
    Document,
    DocumentStatus,
    DocumentClassification,
    DocumentFeedback,
    PDFCache,
    OCRData,
    EmbeddingMetadata,
    Entity,
)

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for Document database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    def get_by_id(self, document_id: str) -> Optional[Document]:
        """
        Get a document by its ID.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Document if found, None otherwise
        """
        return self._db.get(Document, document_id)

    def exists(self, document_id: str) -> bool:
        """
        Check if a document exists.

        Args:
            document_id: Document ID

        Returns:
            True if document exists, False otherwise
        """
        document = self.get_by_id(document_id)
        return document is not None

    def create(
        self,
        document_id: str,
        filename: str,
        file_content: bytes,
        file_size: int,
        mime_type: str,
        user_id: Optional[int] = None,
        status: DocumentStatus = DocumentStatus.PROCESSING,
    ) -> Document:
        """
        Create a new document record.

        Args:
            document_id: Document ID (SHA256 hash)
            filename: Original filename
            file_content: File content as bytes
            file_size: File size in bytes
            mime_type: MIME type
            user_id: User ID who uploaded the document (optional)
            status: Document status (default: PROCESSING)

        Returns:
            Created Document record
        """
        document = Document(
            id=document_id,
            filename=filename,
            file_content=file_content,
            file_size=file_size,
            mime_type=mime_type,
            user_id=user_id,
            status=status,
        )
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document

    def update_status(
        self,
        document: Document,
        status: DocumentStatus,
    ) -> Document:
        """
        Update document status.

        Args:
            document: Document to update
            status: New status

        Returns:
            Updated Document record
        """
        document.status = status
        document.updated_at = datetime.now(timezone.utc)
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document

    def delete(
        self,
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Delete a document and all its related records.
        Handles cascading deletes for all tables that reference the document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Dict with deletion counts and success status

        Raises:
            ValueError: If document not found
        """
        # First, check if document exists
        document = self.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        deletion_counts = {
            "document": 0,
            "classifications": 0,
            "feedback": 0,
            "pdf_cache": 0,
            "upload_session_files": 0,
            "ocr_data": 0,
            "embedding_metadata": 0,
        }

        try:
            # Delete related records first (respecting foreign key constraints)
            # Order matters: delete child records before parent records

            # 1. Delete Entity records (via EmbeddingMetadata)
            metadata_stmt = select(EmbeddingMetadata).where(
                EmbeddingMetadata.document_id == document_id
            )
            metadata_list = list(self._db.exec(metadata_stmt).all())
            
            for metadata in metadata_list:
                # Delete related Entity records first
                entity_stmt = select(Entity).where(
                    Entity.embedding_metadata_id == metadata.id
                )
                entities = list(self._db.exec(entity_stmt).all())
                for entity in entities:
                    self._db.delete(entity)
                deletion_counts["embedding_metadata"] += 1
            
            # Delete EmbeddingMetadata records
            for metadata in metadata_list:
                self._db.delete(metadata)

            # 2. Delete DocumentClassifications
            classification_stmt = select(DocumentClassification).where(
                DocumentClassification.document_id == document_id
            )
            classifications = list(self._db.exec(classification_stmt).all())
            for classification in classifications:
                self._db.delete(classification)
            deletion_counts["classifications"] = len(classifications)

            # 3. Delete DocumentFeedback
            feedback_stmt = select(DocumentFeedback).where(
                DocumentFeedback.document_id == document_id
            )
            feedbacks = list(self._db.exec(feedback_stmt).all())
            for feedback in feedbacks:
                self._db.delete(feedback)
            deletion_counts["feedback"] = len(feedbacks)

            # 4. Delete PDFCache
            pdf_cache_stmt = select(PDFCache).where(
                PDFCache.document_id == document_id
            )
            pdf_cache = self._db.exec(pdf_cache_stmt).first()
            if pdf_cache:
                self._db.delete(pdf_cache)
                deletion_counts["pdf_cache"] = 1

            # 5. Delete OCRData
            ocr_stmt = select(OCRData).where(
                OCRData.document_id == document_id
            )
            ocr_records = list(self._db.exec(ocr_stmt).all())
            for ocr_record in ocr_records:
                self._db.delete(ocr_record)
            deletion_counts["ocr_data"] = len(ocr_records)

            # 6. Finally, delete the Document itself
            self._db.delete(document)
            deletion_counts["document"] = 1

            # Commit all deletions
            self._db.commit()

            logger.info(
                f"Successfully deleted document {document_id} and {sum(deletion_counts.values())} related records"
            )

            return {
                "success": True,
                "message": f"Document '{document.filename}' and all associated data deleted successfully",
                "deletion_counts": deletion_counts,
                "document_id": document_id,
            }

        except Exception as e:
            logger.error(f"Error deleting document {document_id} and related records: {e}")
            self._db.rollback()
            raise

