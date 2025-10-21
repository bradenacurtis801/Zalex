"""
OCR data service for managing extracted text and metadata.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from sqlmodel import select, Session

from src.models.database import OCRData, Document
from src.models.schemas.ocr import OCRDataResponse, OCRWordData, OCRLineData
from src.ocr.tesseract_engine import TesseractEngine

logger = logging.getLogger(__name__)


class OCRService:
    """Service for managing OCR data operations."""

    def __init__(self, db: Session, ocr_engine: TesseractEngine):
        self.db = db
        self.ocr_engine = ocr_engine

    def save_ocr_data(
        self, 
        document_id: str, 
        page_number: int, 
        ocr_result: Dict[str, Any]
    ) -> OCRData:
        """
        Save OCR data for a specific page of a document.
        
        Args:
            document_id: Document ID (SHA256 hash)
            page_number: Page number (0-indexed)
            ocr_result: OCR result from TesseractEngine.extract_text_with_data()
            
        Returns:
            OCRData: The saved OCR data record
        """
        logger.info(f"Saving OCR data for document {document_id}, page {page_number}")
        
        # Calculate average confidence
        words = ocr_result.get('words', [])
        confidence_score = 0.0
        if words:
            total_confidence = sum(word.get('confidence', 0) for word in words)
            confidence_score = total_confidence / len(words) / 100.0  # Convert to 0-1 range
        
        # Create OCR data record
        ocr_data = OCRData(
            document_id=document_id,
            page_number=page_number,
            full_text=ocr_result.get('text', ''),
            words_data=json.dumps(ocr_result.get('words', [])),
            lines_data=json.dumps(ocr_result.get('lines', [])),
            confidence_score=confidence_score,
            total_words=ocr_result.get('total_words', 0),
            total_lines=ocr_result.get('total_lines', 0)
        )
        
        # Save to database
        self.db.add(ocr_data)
        self.db.commit()
        self.db.refresh(ocr_data)
        
        logger.info(f"Successfully saved OCR data for document {document_id}, page {page_number}")
        return ocr_data

    def get_ocr_data_by_document(self, document_id: str) -> List[OCRData]:
        """
        Get all OCR data for a document, ordered by page number.
        
        Args:
            document_id: Document ID (SHA256 hash)
            
        Returns:
            List[OCRData]: List of OCR data records
        """
        stmt = select(OCRData).where(OCRData.document_id == document_id).order_by(OCRData.page_number)
        return self.db.exec(stmt).all()

    def get_document_ocr_data(self, document_id: str) -> List[OCRDataResponse]:
        """
        Get formatted OCR data response for a document.
        
        Args:
            document_id: Document ID (SHA256 hash)
            
        Returns:
            List[OCRDataResponse]: Formatted OCR data responses
        """
        ocr_data_list = self.get_ocr_data_by_document(document_id)
        response_data = []
        
        for ocr_data in ocr_data_list:
            # Get parsed words and lines data
            words_data = self.get_words_data(ocr_data)
            lines_data = self.get_lines_data(ocr_data)
            
            # Convert to response models
            words_response = [OCRWordData(**word) for word in words_data]
            lines_response = [OCRLineData(**line) for line in lines_data]
            
            response_data.append(OCRDataResponse(
                id=ocr_data.id,
                page_number=ocr_data.page_number,
                full_text=ocr_data.full_text,
                confidence_score=ocr_data.confidence_score,
                total_words=ocr_data.total_words,
                total_lines=ocr_data.total_lines,
                words_data=words_response,
                lines_data=lines_response,
                original_image_width=ocr_data.original_image_width,
                original_image_height=ocr_data.original_image_height,
                created_at=ocr_data.created_at
            ))
        
        return response_data

    def get_ocr_data_by_page(self, document_id: str, page_number: int) -> Optional[OCRData]:
        """
        Get OCR data for a specific page of a document.
        
        Args:
            document_id: Document ID (SHA256 hash)
            page_number: Page number (0-indexed)
            
        Returns:
            Optional[OCRData]: OCR data record if found, None otherwise
        """
        stmt = select(OCRData).where(
            OCRData.document_id == document_id,
            OCRData.page_number == page_number
        )
        return self.db.exec(stmt).first()

    def get_words_data(self, ocr_data: OCRData) -> List[Dict[str, Any]]:
        """
        Get parsed words data from OCR data record.
        
        Args:
            ocr_data: OCRData record
            
        Returns:
            List[Dict[str, Any]]: Parsed words data
        """
        try:
            return json.loads(ocr_data.words_data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse words data: {e}")
            return []

    def get_lines_data(self, ocr_data: OCRData) -> List[Dict[str, Any]]:
        """
        Get parsed lines data from OCR data record.
        
        Args:
            ocr_data: OCRData record
            
        Returns:
            List[Dict[str, Any]]: Parsed lines data
        """
        try:
            return json.loads(ocr_data.lines_data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse lines data: {e}")
            return []

    def search_text_in_document(
        self, 
        document_id: str, 
        search_term: str, 
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for text within a document's OCR data.
        
        Args:
            document_id: Document ID (SHA256 hash)
            search_term: Text to search for
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List[Dict[str, Any]]: List of matches with page and position info
        """
        logger.info(f"Searching for '{search_term}' in document {document_id}")
        
        ocr_data_list = self.get_ocr_data_by_document(document_id)
        matches = []
        
        search_term_lower = search_term.lower() if not case_sensitive else search_term
        
        for ocr_data in ocr_data_list:
            page_text = ocr_data.full_text
            if not case_sensitive:
                page_text = page_text.lower()
            
            if search_term_lower in page_text:
                # Find all occurrences on this page
                start = 0
                while True:
                    pos = page_text.find(search_term_lower, start)
                    if pos == -1:
                        break
                    
                    matches.append({
                        'page_number': ocr_data.page_number,
                        'position': pos,
                        'text': ocr_data.full_text[pos:pos + len(search_term)],
                        'confidence': ocr_data.confidence_score
                    })
                    start = pos + 1
        
        logger.info(f"Found {len(matches)} matches for '{search_term}' in document {document_id}")
        return matches

    def get_document_text_summary(self, document_id: str) -> Dict[str, Any]:
        """
        Get a summary of all text content in a document.
        
        Args:
            document_id: Document ID (SHA256 hash)
            
        Returns:
            Dict[str, Any]: Document text summary
        """
        ocr_data_list = self.get_ocr_data_by_document(document_id)
        
        if not ocr_data_list:
            return {
                'total_pages': 0,
                'total_words': 0,
                'total_lines': 0,
                'average_confidence': 0.0,
                'full_text': ''
            }
        
        total_words = sum(ocr.total_words for ocr in ocr_data_list)
        total_lines = sum(ocr.total_lines for ocr in ocr_data_list)
        total_confidence = sum(ocr.confidence_score for ocr in ocr_data_list)
        average_confidence = total_confidence / len(ocr_data_list) if ocr_data_list else 0.0
        
        # Combine all text
        full_text = '\n\n'.join(ocr.full_text for ocr in ocr_data_list)
        
        return {
            'total_pages': len(ocr_data_list),
            'total_words': total_words,
            'total_lines': total_lines,
            'average_confidence': average_confidence,
            'full_text': full_text
        }

    def delete_ocr_data(self, document_id: str) -> int:
        """
        Delete all OCR data for a document.
        
        Args:
            document_id: Document ID (SHA256 hash)
            
        Returns:
            int: Number of records deleted
        """
        logger.info(f"Deleting OCR data for document {document_id}")
        
        stmt = select(OCRData).where(OCRData.document_id == document_id)
        ocr_data_list = self.db.exec(stmt).all()
        
        for ocr_data in ocr_data_list:
            self.db.delete(ocr_data)
        
        self.db.commit()
        
        deleted_count = len(ocr_data_list)
        logger.info(f"Deleted {deleted_count} OCR data records for document {document_id}")
        return deleted_count
