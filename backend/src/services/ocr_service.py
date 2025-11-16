"""
OCR data service for managing extracted text and metadata.
"""

import json
import logging
from typing import List, Dict, Any

from src.models.database import OCRData
from src.models.schemas.ocr import (
    OCRDataResponse,
    OCRWordData,
    OCRLineData,
    PageOCRDataResponse,
    DocumentOCRDataResponse,
    OCRSearchResponse,
    OCRSearchMatch,
    OCRSummaryResponse,
    DocumentTextSummary,
)
from src.core.exceptions import DocumentNotFoundError
from scanpro_lib.ocr.tesseract_engine import TesseractEngine
from src.repositories.ocr_data_repository import OCRDataRepository

logger = logging.getLogger(__name__)


class OCRService:
    """Service for managing OCR data operations."""

    def __init__(
        self,
        ocr_engine: TesseractEngine,
        ocr_data_repo: OCRDataRepository,
    ):
        self.ocr_engine = ocr_engine
        self.ocr_data_repo = ocr_data_repo

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
        

        ocr_data = self.ocr_data_repo.create(
            document_id=document_id,
            page_number=page_number,
            full_text=ocr_result.get('text', ''),
            words_data=json.dumps(ocr_result.get('words', [])),
            lines_data=json.dumps(ocr_result.get('lines', [])),
            confidence_score=confidence_score,
            total_words=ocr_result.get('total_words', 0),
            total_lines=ocr_result.get('total_lines', 0),
        )

        
        logger.info(f"Successfully saved OCR data for document {document_id}, page {page_number}")
        return ocr_data



    def get_document_ocr_data(self, document_id: str) -> DocumentOCRDataResponse:
        """
        Get formatted OCR data response for a document.
        
        Args:
            document_id: Document ID (SHA256 hash)
            
        Returns:
            DocumentOCRDataResponse: Formatted OCR data response for the document
        """
        ocr_data_list = self.ocr_data_repo.get_by_document_id(document_id)
        response_data = []
        
        for ocr_data in ocr_data_list:
            # Get parsed words and lines data
            words_data = self.get_words_data(ocr_data)
            lines_data = self.get_lines_data(ocr_data)
            
            # Convert to response models with backward compatibility
            words_response = self._convert_words_to_response(words_data)
            lines_response = self._convert_lines_to_response(lines_data)
            
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
        
        return DocumentOCRDataResponse(
            document_id=document_id,
            total_pages=len(response_data),
            ocr_data=response_data
        )



    def get_page_ocr_data(self, document_id: str, page_number: int) -> PageOCRDataResponse:
        """
        Get formatted OCR data response for a specific page.
        
        Args:
            document_id: Document ID (SHA256 hash)
            page_number: Page number (0-indexed)
            
        Returns:
            PageOCRDataResponse: Formatted OCR data response
            
        Raises:
            DocumentNotFoundError: If OCR data for the page is not found
        """
        ocr_data = self.ocr_data_repo.get_by_page(document_id, page_number)
        
        if not ocr_data:
            raise DocumentNotFoundError(
                f"OCR data not found for document {document_id}, page {page_number}"
            )
        
        # Get parsed words and lines data
        words_data = self.get_words_data(ocr_data)
        lines_data = self.get_lines_data(ocr_data)
        
        # Convert to response models with backward compatibility
        words_response = self._convert_words_to_response(words_data)
        lines_response = self._convert_lines_to_response(lines_data)
        
        return PageOCRDataResponse(
            id=ocr_data.id,
            document_id=ocr_data.document_id,
            page_number=ocr_data.page_number,
            full_text=ocr_data.full_text,
            confidence_score=ocr_data.confidence_score,
            total_words=ocr_data.total_words,
            total_lines=ocr_data.total_lines,
            words_data=words_response,
            lines_data=lines_response,
            created_at=ocr_data.created_at
        )

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

    def _convert_words_to_response(self, words_data: List[Dict[str, Any]]) -> List[OCRWordData]:
        """
        Convert words data to OCRWordData response models with backward compatibility.
        
        Args:
            words_data: List of word dictionaries
            
        Returns:
            List[OCRWordData]: Converted word response models
        """
        words_response = []
        for word in words_data:
            # Ensure all required fields are present (backward compatibility)
            word_dict = {
                'text': word.get('text', ''),
                'confidence': word.get('confidence', 0),
                'bbox': word.get('bbox', {'left': 0, 'top': 0, 'width': 0, 'height': 0}),
                'block_num': word.get('block_num', 0),
                'par_num': word.get('par_num', 0),
                'line_num': word.get('line_num', 0),
                'word_num': word.get('word_num', 0)
            }
            words_response.append(OCRWordData(**word_dict))
        return words_response

    def _convert_lines_to_response(self, lines_data: List[Dict[str, Any]]) -> List[OCRLineData]:
        """
        Convert lines data to OCRLineData response models with backward compatibility.
        
        Args:
            lines_data: List of line dictionaries
            
        Returns:
            List[OCRLineData]: Converted line response models
        """
        lines_response = []
        for line in lines_data:
            # Ensure all required fields are present (backward compatibility)
            line_dict = {
                'text': line.get('text', ''),
                'confidence': line.get('confidence', 0.0),
                'bbox': line.get('bbox', {'left': 0, 'top': 0, 'width': 0, 'height': 0}),
                'words': line.get('words', []),
                'block_num': line.get('block_num', 0),
                'par_num': line.get('par_num', 0),
                'line_num': line.get('line_num', 0)
            }
            # Also ensure words in the line have all required fields
            if 'words' in line_dict and line_dict['words']:
                processed_words = []
                for word in line_dict['words']:
                    word_dict = {
                        'text': word.get('text', ''),
                        'confidence': word.get('confidence', 0),
                        'bbox': word.get('bbox', {'left': 0, 'top': 0, 'width': 0, 'height': 0}),
                        'block_num': word.get('block_num', 0),
                        'par_num': word.get('par_num', 0),
                        'line_num': word.get('line_num', 0),
                        'word_num': word.get('word_num', 0)
                    }
                    processed_words.append(word_dict)
                line_dict['words'] = processed_words
            lines_response.append(OCRLineData(**line_dict))
        return lines_response

    def search_text_in_document(
        self, 
        document_id: str, 
        search_term: str, 
        case_sensitive: bool = False
    ) -> OCRSearchResponse:
        """
        Search for text within a document's OCR data.
        
        Args:
            document_id: Document ID (SHA256 hash)
            search_term: Text to search for
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            OCRSearchResponse: Search results with matches and metadata
        """
        logger.info(f"Searching for '{search_term}' in document {document_id}")
        
        ocr_data_list = self.ocr_data_repo.get_by_document_id(document_id)
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
                    
                    matches.append(OCRSearchMatch(
                        page_number=ocr_data.page_number,
                        position=pos,
                        text=ocr_data.full_text[pos:pos + len(search_term)],
                        confidence=ocr_data.confidence_score
                    ))
                    start = pos + 1
        
        logger.info(f"Found {len(matches)} matches for '{search_term}' in document {document_id}")
        
        return OCRSearchResponse(
            document_id=document_id,
            query=search_term,
            case_sensitive=case_sensitive,
            total_matches=len(matches),
            matches=matches
        )

    def get_document_text_summary(self, document_id: str) -> OCRSummaryResponse:
        """
        Get a summary of all text content in a document.
        
        Args:
            document_id: Document ID (SHA256 hash)
            
        Returns:
            OCRSummaryResponse: Document text summary response
        """
        ocr_data_list = self.ocr_data_repo.get_by_document_id(document_id)
        
        if not ocr_data_list:
            summary = DocumentTextSummary(
                total_pages=0,
                total_words=0,
                total_lines=0,
                average_confidence=0.0,
                full_text=''
            )
        else:
            total_words = sum(ocr.total_words for ocr in ocr_data_list)
            total_lines = sum(ocr.total_lines for ocr in ocr_data_list)
            total_confidence = sum(ocr.confidence_score for ocr in ocr_data_list)
            average_confidence = total_confidence / len(ocr_data_list) if ocr_data_list else 0.0
            
            # Combine all text
            full_text = '\n\n'.join(ocr.full_text for ocr in ocr_data_list)
            
            summary = DocumentTextSummary(
                total_pages=len(ocr_data_list),
                total_words=total_words,
                total_lines=total_lines,
                average_confidence=average_confidence,
                full_text=full_text
            )
        
        return OCRSummaryResponse(
            document_id=document_id,
            summary=summary
        )
