"""
OCR data API endpoints.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from src.dependencies import get_db, get_ocr_service, get_current_user
from src.services.ocr_service import OCRService
from src.models.database import OCRData, User
from src.models.schemas.ocr import (
    DocumentOCRDataResponse,
    OCRDataResponse,
    PageOCRDataResponse,
    OCRSearchResponse,
    OCRSearchMatch,
    OCRSummaryResponse,
    DocumentTextSummary,
    OCRWordData,
    OCRLineData
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
    
    response_data = ocr_service.get_document_ocr_data(document_id)
    
    return DocumentOCRDataResponse(
        document_id=document_id,
        total_pages=len(response_data),
        ocr_data=response_data
    )


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
    
    ocr_data = ocr_service.get_ocr_data_by_page(document_id, page_number)
    
    if not ocr_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OCR data not found for document {document_id}, page {page_number}"
        )
    
    # Get parsed words and lines data
    words_data = ocr_service.get_words_data(ocr_data)
    lines_data = ocr_service.get_lines_data(ocr_data)
    
    # Convert to response models
    words_response = [OCRWordData(**word) for word in words_data]
    lines_response = [OCRLineData(**line) for line in lines_data]
    
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
    
    matches = ocr_service.search_text_in_document(
        document_id, 
        query, 
        case_sensitive
    )
    
    # Convert to response models
    matches_response = [OCRSearchMatch(**match) for match in matches]
    
    return OCRSearchResponse(
        document_id=document_id,
        query=query,
        case_sensitive=case_sensitive,
        total_matches=len(matches_response),
        matches=matches_response
    )


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
    
    summary_data = ocr_service.get_document_text_summary(document_id)
    
    summary = DocumentTextSummary(**summary_data)
    
    return OCRSummaryResponse(
        document_id=document_id,
        summary=summary
    )
