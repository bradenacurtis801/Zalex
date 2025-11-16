import logging
import os
import uuid
from typing import Optional

import config
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, Response
from src.dependencies import (
    get_pdf_service, 
    get_upload_service, 
    get_current_user, 
    require_admin,
    validate_uploaded_files
)
from src.models.database import User
from src.models.schemas.upload import UploadResponse
from src.services.pdf_service import PDFService
from src.services.upload_service import UploadService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    validated_files: list[UploadFile] = Depends(validate_uploaded_files),
    upload_service: UploadService = Depends(get_upload_service),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    """
    Handles the file upload and initiates the processing pipeline.
    
    Only PDF and image files (.pdf, .jpg, .jpeg, .png) are supported.
    Text files (.txt) are explicitly rejected.
    """
    logger.info(f"Received upload request with {len(validated_files)} file(s) from user {current_user.id}")
    
    # Files are already validated by the dependency
    return await upload_service.process_upload(validated_files, current_user.id)


@router.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: str,
    pdf_service: PDFService = Depends(get_pdf_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get the content of a document for viewing.

    Args:
        document_id: Document ID (SHA256 hash)
        pdf_service: PDF service instance
        current_user: Authenticated user

    Returns:
        File content or text content
    """
    logger.info(f"Received request for document content: {document_id} from user {current_user.id}")
    return pdf_service.get_document_content_response(document_id)


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    pdf_service: PDFService = Depends(get_pdf_service),
    current_user: User = Depends(get_current_user),
):
    """
    Download a document file.

    Args:
        document_id: Document ID (SHA256 hash)
        pdf_service: PDF service instance
        current_user: Authenticated user

    Returns:
        File download response
    """
    logger.info(f"Received download request for: {document_id} from user {current_user.id}")
    return pdf_service.get_document_download_response(document_id)


@router.get("/documents/{document_id}/pages")
async def get_pdf_pages(
    document_id: str,
    pages: Optional[str] = Query(None, description="Comma-separated list of page numbers to fetch (e.g., '1,3,5'). If not provided, returns all pages."),
    pdf_service: PDFService = Depends(get_pdf_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get PDF pages with caching - first check cache, then convert if needed.
    Can fetch specific pages or all pages.

    Args:
        document_id: Document ID (SHA256 hash)
        pages: Optional comma-separated list of page numbers (1-based) to fetch
        pdf_service: PDF service instance
        current_user: Authenticated user

    Returns:
        JSON with page information and image data
    """
    logger.info(f"Received request for PDF pages: document_id={document_id}, pages={pages} from user {current_user.id}")
    return pdf_service.get_pdf_pages(document_id, pages)



@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    upload_service: UploadService = Depends(get_upload_service),
    current_user: User = Depends(require_admin()),
):
    """
    Delete a document and all its associated data (admin only).

    Args:
        document_id: Document ID (SHA256 hash)
        upload_service: Upload service instance
        current_user: Authenticated admin user

    Returns:
        Success message with deletion details
    """
    logger.info(f"Received delete request for document: {document_id} from user {current_user.id}")
    return await upload_service.delete_document(document_id)


# PROBABLY NOT NEEDED

# @router.get("/pdf-cache/stats")
# async def get_pdf_cache_stats(pdf_service: PDFService = Depends(get_pdf_service)):
#     """
#     Get PDF cache statistics.

#     Args:
#         pdf_service: PDF service instance

#     Returns:
#         Cache statistics
#     """
#     logger.info("Received request for PDF cache stats")

#     try:
#         stats = pdf_service.get_cache_stats()
#         return stats

#     except Exception as e:
#         logger.error(f"Error getting cache stats: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Failed to get cache stats: {str(e)}"
#         )


# PROBABLY NOT NEEDED

# @router.post("/pdf-cache/cleanup")
# async def cleanup_pdf_cache(pdf_service: PDFService = Depends(get_pdf_service)):
#     """
#     Clean up expired PDF cache files.

#     Args:
#         pdf_service: PDF service instance

#     Returns:
#         Cleanup results
#     """
#     logger.info("Received request to cleanup PDF cache")

#     try:
#         cleaned_count = pdf_service.cleanup_expired_cache()
#         return {
#             "success": True,
#             "cleaned_files": cleaned_count,
#             "message": f"Cleaned up {cleaned_count} expired cache files",
#         }

#     except Exception as e:
#         logger.error(f"Error cleaning up cache: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Failed to cleanup cache: {str(e)}"
#         )
