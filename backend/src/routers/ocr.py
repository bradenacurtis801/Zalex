"""
OCR data API endpoints.
"""

import logging

from fastapi import APIRouter, Depends, Query

from src.dependencies import get_ocr_service, get_current_user
from src.services.ocr_service import OCRService
from src.models.database import User
from src.models.schemas.ocr import (
    DocumentOCRDataResponse,
    PageOCRDataResponse,
    OCRSearchResponse,
    OCRSummaryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/documents/{document_id}/ocr", response_model=DocumentOCRDataResponse)
async def get_document_ocr_data(
    document_id: str,
    ocr_service: OCRService = Depends(get_ocr_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get all OCR data for a document.
    
    Args:
        document_id: Document ID (SHA256 hash)
        ocr_service: OCR service instance
        
    Returns:
        DocumentOCRDataResponse with all OCR data for the document
    """
    logger.info(f"Getting OCR data for document: {document_id}")
    return ocr_service.get_document_ocr_data(document_id)


@router.get("/documents/{document_id}/ocr/pages/{page_number}", response_model=PageOCRDataResponse)
async def get_page_ocr_data(
    document_id: str,
    page_number: int,
    ocr_service: OCRService = Depends(get_ocr_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get OCR data for a specific page of a document.
    
    Args:
        document_id: Document ID (SHA256 hash)
        page_number: Page number (0-indexed)
        ocr_service: OCR service instance
        
    Returns:
        PageOCRDataResponse with detailed OCR data for the specified page
    """
    logger.info(f"Getting OCR data for document {document_id}, page {page_number}")
    return ocr_service.get_page_ocr_data(document_id, page_number)


@router.get("/documents/{document_id}/ocr/search", response_model=OCRSearchResponse)
async def search_document_text(
    document_id: str,
    query: str = Query(..., description="Text to search for"),
    case_sensitive: bool = Query(False, description="Whether search should be case sensitive"),
    ocr_service: OCRService = Depends(get_ocr_service),
    current_user: User = Depends(get_current_user),
):
    """
    Search for text within a document's OCR data.
    
    Args:
        document_id: Document ID (SHA256 hash)
        query: Text to search for
        case_sensitive: Whether search should be case sensitive
        ocr_service: OCR service instance
        
    Returns:
        OCRSearchResponse with search matches and metadata
    """
    logger.info(f"Searching for '{query}' in document {document_id}")
    return ocr_service.search_text_in_document(document_id, query, case_sensitive)


@router.get("/documents/{document_id}/ocr/summary", response_model=OCRSummaryResponse)
async def get_document_text_summary(
    document_id: str,
    ocr_service: OCRService = Depends(get_ocr_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get a summary of all text content in a document.
    
    Args:
        document_id: Document ID (SHA256 hash)
        ocr_service: OCR service instance
        
    Returns:
        OCRSummaryResponse with document text summary
    """
    logger.info(f"Getting text summary for document: {document_id}")
    return ocr_service.get_document_text_summary(document_id)
