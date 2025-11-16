"""PDF processing service for converting PDFs to images."""

import json
import logging
from typing import Any, Dict, List, Optional

from src.models.database import Document
from scanpro_lib.utils.pdf_helper import PDFHelper, PDFPage
from fastapi.responses import Response, JSONResponse
from src.repositories.document_repository import DocumentRepository
from src.repositories.document_classification_repository import DocumentClassificationRepository
from src.repositories.pdf_cache_repository import PDFCacheRepository

logger = logging.getLogger(__name__)


class PDFService:
    """Service for handling PDF operations with database caching."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        classification_repo: DocumentClassificationRepository,
        pdf_cache_repo: PDFCacheRepository,
    ):
        """
        Initialize the PDF service.
        
        Args:
            document_repo: Document repository
            classification_repo: Document classification repository
            pdf_cache_repo: PDF cache repository
        """
        self.document_repo = document_repo
        self.classification_repo = classification_repo
        self.pdf_cache_repo = pdf_cache_repo

    def get_pdf_pages(
        self, document_id: str, pages: Optional[str] = None
    ) -> JSONResponse:
        """
        Get PDF pages with caching - first check cache, then convert if needed.
        Can filter to specific pages if requested.

        Args:
            document_id: Document ID (file hash)
            pages: Optional comma-separated string of page numbers (0-indexed, e.g., "0,2,4") to filter. If None, returns all pages.

        Returns:
            JSONResponse with page information and image data

        Raises:
            FileNotFoundError: If the document doesn't exist
            ValueError: If the file is not a PDF or invalid page numbers
            Exception: If conversion fails
        """
        # Parse pages parameter if provided (0-indexed)
        page_numbers: Optional[List[int]] = None
        if pages:
            page_numbers = [int(p.strip()) for p in pages.split(',') if p.strip()]
            if any(p < 0 for p in page_numbers):
                raise ValueError("Page numbers must be non-negative integers (0-based)")
        
        logger.info(f"Getting PDF pages for document ID: {document_id}, requested pages: {page_numbers}")

        # First, try to get from cache
        cached_data = self.pdf_cache_repo.get_by_document_id(document_id)
        if cached_data:
            logger.info(f"Using cached PDF pages for document {document_id}")

            
            # Get document category (may have changed since cache was created)
            category = None
            classification = self.classification_repo.get_by_document_id(document_id)
            if classification:
                category = classification.category
            cached_data["category"] = category
            
            # Filter to requested pages if specified
            if page_numbers:
                all_pages = cached_data.get("pages", [])
                filtered_pages = [p for p in all_pages if p.get("page_number") in page_numbers]
                
                # Check if any requested pages are missing
                found_page_numbers = {p.get("page_number") for p in filtered_pages}
                missing_pages = set(page_numbers) - found_page_numbers
                if missing_pages:
                    logger.warning(f"Requested pages {missing_pages} not found in cached data for document {document_id}")
                
                # Create filtered response
                filtered_data = cached_data.copy()
                filtered_data["pages"] = filtered_pages
                filtered_data["returned_pages"] = len(filtered_pages)
                filtered_data["has_more_pages"] = False  # When filtering, we return exactly what was requested
                
                return self._to_json_response(filtered_data, document_id)
            
            return self._to_json_response(cached_data, document_id)

        # Cache miss - get document and convert
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found")

        # Check if it's a PDF
        if not document.mime_type.startswith("application/pdf"):
            raise ValueError(f"Document is not a PDF: {document.filename}")

        try:
            # Get actual total page count first
            actual_total_pages = PDFHelper.get_page_count(document.file_content)
            
            # Convert PDF to images in memory (all pages) - always convert all for caching
            pages = self._convert_pdf_to_images_in_memory(document.file_content)

            if not pages:
                raise Exception("Failed to convert PDF to images")

            # Get document category (latest classification)
            category = None
            classification = self.classification_repo.get_by_document_id(document_id)
            if classification:
                category = classification.category

            # Create full result with all pages for caching
            full_result = {
                "filename": document.filename, 
                "total_pages": actual_total_pages,  # Actual total pages in PDF
                "returned_pages": len(pages),  # Number of pages in full result
                "has_more_pages": False,  # All pages are always returned
                "category": category,  # Document category from classification
                "pages": pages
            }

            # Cache all pages in database (for future requests)
            self.pdf_cache_repo.upsert(document_id, full_result)
            logger.info(f"Cached all {len(pages)} pages for document {document_id}")

            # Filter to requested pages if specified, otherwise return all
            if page_numbers:
                filtered_pages = [p for p in pages if p.get("page_number") in page_numbers]
                
                # Check if any requested pages are missing
                found_page_numbers = {p.get("page_number") for p in filtered_pages}
                missing_pages = set(page_numbers) - found_page_numbers
                if missing_pages:
                    logger.warning(f"Requested pages {missing_pages} not found in document {document_id} (total pages: {actual_total_pages})")
                
                # Return only requested pages
                filtered_result = {
                    "filename": document.filename,
                    "total_pages": actual_total_pages,
                    "returned_pages": len(filtered_pages),
                    "has_more_pages": False,
                    "category": category,
                    "pages": filtered_pages
                }
                
                return self._to_json_response(filtered_result, document_id)

            # Return all pages if no filter specified
            return self._to_json_response(full_result, document_id)

        except Exception as e:
            logger.error(f"Error converting PDF to pages: {e}")
            raise Exception(f"Failed to convert PDF: {str(e)}")

    def _to_json_response(self, data: Dict[str, Any], document_id: str) -> JSONResponse:
        """
        Convert data to JSONResponse with caching headers.

        Args:
            data: The data to return
            document_id: Document ID for ETag

        Returns:
            JSONResponse with caching headers
        """
        response = JSONResponse(content=data)
        response.headers["Cache-Control"] = "public, max-age=3600"  # Cache for 1 hour
        response.headers["ETag"] = f'"{document_id}"'  # Use document_id as ETag
        return response

    def _to_content_response(self, content: bytes, media_type: str, filename: str, disposition: str) -> Response:
        """
        Convert content to Response with proper headers.

        Args:
            content: The file content
            media_type: MIME type
            filename: Original filename
            disposition: Content disposition (inline/attachment)

        Returns:
            Response with proper headers
        """
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"{disposition}; filename={filename}"},
        )

    def convert_pdf_to_pages(
        self, document_id: str
    ) -> Dict[str, Any]:
        """
        Convert a PDF document to images and return page information.
        This method bypasses cache and always converts fresh.
        Always converts all pages in the PDF.

        Args:
            document_id: Document ID (file hash)

        Returns:
            Dictionary with page information and image data

        Raises:
            FileNotFoundError: If the document doesn't exist
            ValueError: If the file is not a PDF
            Exception: If conversion fails
        """
        logger.info(f"Converting PDF to pages for document ID: {document_id}")

        # Get document from database
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found")

        # Check if it's a PDF
        if not document.mime_type.startswith("application/pdf"):
            raise ValueError(f"Document is not a PDF: {document.filename}")

        try:
            # Get actual total page count first
            actual_total_pages = PDFHelper.get_page_count(document.file_content)
            
            # Convert PDF to images in memory (all pages)
            pages = self._convert_pdf_to_images_in_memory(document.file_content)

            if not pages:
                raise Exception("Failed to convert PDF to images")

            result = {
                "filename": document.filename, 
                "total_pages": actual_total_pages,  # Actual total pages in PDF
                "returned_pages": len(pages),  # Number of pages returned in this response
                "has_more_pages": False,  # All pages are always returned
                "pages": pages
            }

            # Cache the result in database
            self.pdf_cache_repo.upsert(document_id, result)

            return result

        except Exception as e:
            logger.error(f"Error converting PDF to pages: {e}")
            raise Exception(f"Failed to convert PDF: {str(e)}")

    def _convert_pdf_to_images_in_memory(
        self, pdf_content: bytes
    ) -> List[Dict[str, Any]]:
        """
        Convert PDF pages to images in memory.
        Always converts all pages.

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            List of page dictionaries with image data
        """
        try:
            pages = []
            
            # Use PDFHelper generator to extract pages
            for pdf_page in PDFHelper.extract_pages(pdf_content):
                pages.append(
                    {
                        "page_number": pdf_page.page_number,
                        "image_data": f"data:image/png;base64,{pdf_page.image_base64}",
                        "width": pdf_page.width,
                        "height": pdf_page.height,
                    }
                )

            logger.info(f"Successfully converted {len(pages)} pages to images")
            return pages

        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []


    def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache records from database.

        Returns:
            Number of records cleaned up
        """
        return self.pdf_cache_repo.delete_expired()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics from database.

        Returns:
            Dictionary with cache statistics
        """
        return self.pdf_cache_repo.get_stats()

    def get_document_content_response(self, document_id: str) -> Response:
        """
        Get document content as a Response object for viewing.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Response object with document content

        Raises:
            FileNotFoundError: If document not found
        """
        logger.info(f"Getting document content: {document_id}")

        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found")

        # Determine file type from MIME type
        mime_type = document.mime_type.lower()

        if mime_type == "application/pdf":
            # For PDFs, return with proper MIME type for browser display
            return self._to_content_response(
                content=document.file_content,
                media_type="application/pdf",
                filename=document.filename,
                disposition="inline"
            )
        elif mime_type.startswith("image/"):
            # For images, return with proper MIME type
            return self._to_content_response(
                content=document.file_content,
                media_type=mime_type,
                filename=document.filename,
                disposition="inline"
            )
        else:
            # For text files, return the content
            try:
                content = document.file_content.decode("utf-8")
                return {"content": content, "filename": document.filename}
            except UnicodeDecodeError:
                # If it's not a text file, return as binary
                return self._to_content_response(
                    content=document.file_content,
                    media_type="application/octet-stream",
                    filename=document.filename,
                    disposition="attachment"
                )

    def get_document_download_response(self, document_id: str) -> Response:
        """
        Get document as a Response object for download.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Response object with document content for download

        Raises:
            FileNotFoundError: If document not found
        """
        logger.info(f"Getting document for download: {document_id}")

        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found")

        return self._to_content_response(
            content=document.file_content,
            media_type=document.mime_type,
            filename=document.filename,
            disposition="attachment"
        )
