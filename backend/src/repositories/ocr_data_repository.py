"""Repository for OCRData database operations."""

import logging
from typing import List, Optional

from sqlmodel import Session, select

from src.models.database import OCRData

logger = logging.getLogger(__name__)


class OCRDataRepository:
    """Repository for OCRData database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    def create(
        self,
        document_id: str,
        page_number: int,
        full_text: str,
        words_data: str,
        lines_data: str,
        confidence_score: float,
        total_words: int,
        total_lines: int,
        original_image_width: Optional[int] = None,
        original_image_height: Optional[int] = None,
    ) -> OCRData:
        """
        Create a new OCRData record.

        Args:
            document_id: Document ID (SHA256 hash)
            page_number: Page number (0-indexed)
            full_text: Full extracted text
            words_data: JSON string of words data
            lines_data: JSON string of lines data
            confidence_score: Average confidence score (0-1)
            total_words: Total number of words
            total_lines: Total number of lines
            original_image_width: Original image width (optional)
            original_image_height: Original image height (optional)

        Returns:
            Created OCRData record
        """
        ocr_data = OCRData(
            document_id=document_id,
            page_number=page_number,
            full_text=full_text,
            words_data=words_data,
            lines_data=lines_data,
            confidence_score=confidence_score,
            total_words=total_words,
            total_lines=total_lines,
            original_image_width=original_image_width,
            original_image_height=original_image_height,
        )
        self._db.add(ocr_data)
        self._db.commit()
        self._db.refresh(ocr_data)
        return ocr_data

    def get_by_document_id(self, document_id: str) -> List[OCRData]:
        """
        Get all OCR data for a document, ordered by page number.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            List of OCRData records
        """
        stmt = (
            select(OCRData)
            .where(OCRData.document_id == document_id)
            .order_by(OCRData.page_number)
        )
        return list(self._db.exec(stmt).all())

    def get_by_page(
        self, document_id: str, page_number: int
    ) -> Optional[OCRData]:
        """
        Get OCR data for a specific page of a document.

        Args:
            document_id: Document ID (SHA256 hash)
            page_number: Page number (0-indexed)

        Returns:
            OCRData record if found, None otherwise
        """
        stmt = select(OCRData).where(
            OCRData.document_id == document_id,
            OCRData.page_number == page_number,
        )
        return self._db.exec(stmt).first()

    def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all OCR data for a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Number of records deleted
        """
        stmt = select(OCRData).where(OCRData.document_id == document_id)
        ocr_data_list = list(self._db.exec(stmt).all())

        for ocr_data in ocr_data_list:
            self._db.delete(ocr_data)

        self._db.commit()
        return len(ocr_data_list)

