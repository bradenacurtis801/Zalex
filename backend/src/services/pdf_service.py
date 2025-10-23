"""PDF processing service for converting PDFs to images."""

import base64
import hashlib
import io
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import config
import fitz  # PyMuPDF
from PIL import Image
from sqlmodel import Session, select

from src.models.database import PDFCache, Document
from fastapi.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class PDFService:
    """Service for handling PDF operations with database caching."""

    def __init__(self, db: Session):
        """Initialize the PDF service."""
        self.db = db

    def get_pdf_pages(
        self, document_id: str, max_pages: int = 20
    ) -> JSONResponse:
        """
        Get PDF pages with caching - first check cache, then convert if needed.

        Args:
            document_id: Document ID (file hash)
            max_pages: Maximum number of pages to convert

        Returns:
            JSONResponse with page information and image data

        Raises:
            FileNotFoundError: If the document doesn't exist
            ValueError: If the file is not a PDF
            Exception: If conversion fails
        """
        logger.info(f"Getting PDF pages for document ID: {document_id}")

        # First, try to get from cache
        cached_data = self._get_from_db_cache(document_id, max_pages)
        if cached_data:
            logger.info(f"Using cached PDF pages for document {document_id}")
            return self._to_json_response(cached_data, document_id, max_pages)

        # Cache miss - get document and convert
        document = self.db.get(Document, document_id)
        if not document:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found")

        # Check if it's a PDF
        if not document.mime_type.startswith("application/pdf"):
            raise ValueError(f"Document is not a PDF: {document.filename}")

        try:
            # Convert PDF to images in memory
            pages = self._convert_pdf_to_images_in_memory(document.file_content, max_pages)

            if not pages:
                raise Exception("Failed to convert PDF to images")

            result = {
                "filename": document.filename, 
                "total_pages": len(pages), 
                "pages": pages
            }

            # Cache the result in database
            self._save_to_db_cache(document_id, max_pages, result)

            return self._to_json_response(result, document_id, max_pages)

        except Exception as e:
            logger.error(f"Error converting PDF to pages: {e}")
            raise Exception(f"Failed to convert PDF: {str(e)}")

    def _to_json_response(self, data: Dict[str, Any], document_id: str, max_pages: int) -> JSONResponse:
        """
        Convert data to JSONResponse with caching headers.

        Args:
            data: The data to return
            document_id: Document ID for ETag
            max_pages: Max pages for ETag

        Returns:
            JSONResponse with caching headers
        """
        response = JSONResponse(content=data)
        response.headers["Cache-Control"] = "public, max-age=3600"  # Cache for 1 hour
        response.headers["ETag"] = f'"{document_id}_{max_pages}"'  # Use document_id + max_pages as ETag
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
        self, document_id: str, max_pages: int = 20
    ) -> Dict[str, Any]:
        """
        Convert a PDF document to images and return page information.
        This method bypasses cache and always converts fresh.

        Args:
            document_id: Document ID (file hash)
            max_pages: Maximum number of pages to convert

        Returns:
            Dictionary with page information and image data

        Raises:
            FileNotFoundError: If the document doesn't exist
            ValueError: If the file is not a PDF
            Exception: If conversion fails
        """
        logger.info(f"Converting PDF to pages for document ID: {document_id}")

        # Get document from database
        document = self.db.get(Document, document_id)
        if not document:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found")

        # Check if it's a PDF
        if not document.mime_type.startswith("application/pdf"):
            raise ValueError(f"Document is not a PDF: {document.filename}")

        try:
            # Convert PDF to images in memory
            pages = self._convert_pdf_to_images_in_memory(document.file_content, max_pages)

            if not pages:
                raise Exception("Failed to convert PDF to images")

            result = {
                "filename": document.filename, 
                "total_pages": len(pages), 
                "pages": pages
            }

            # Cache the result in database
            self._save_to_db_cache(document_id, max_pages, result)

            return result

        except Exception as e:
            logger.error(f"Error converting PDF to pages: {e}")
            raise Exception(f"Failed to convert PDF: {str(e)}")

    def _convert_pdf_to_images_in_memory(
        self, pdf_content: bytes, max_pages: int
    ) -> List[Dict[str, Any]]:
        """
        Convert PDF pages to images in memory.

        Args:
            pdf_content: PDF file content as bytes
            max_pages: Maximum number of pages to convert

        Returns:
            List of page dictionaries with image data
        """
        try:
            # Open the PDF from memory
            pdf_document: fitz.Document = fitz.open(stream=pdf_content, filetype="pdf")
            total_pages = pdf_document.page_count
            pages_to_convert = min(total_pages, max_pages)

            logger.info(
                f"PDF has {total_pages} pages, converting first {pages_to_convert}"
            )

            pages = []

            for page_num in range(pages_to_convert):
                try:
                    # Get the page
                    page = pdf_document[page_num]

                    # Convert to image with high DPI for better quality
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)

                    # Convert to PIL Image
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    # Get image dimensions
                    width, height = img.size

                    # Convert image to base64 for direct serving
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format="PNG")
                    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

                    pages.append(
                        {
                            "page_number": page_num + 1,
                            "image_data": f"data:image/png;base64,{img_base64}",
                            "width": width,
                            "height": height,
                        }
                    )

                    logger.debug(f"Converted page {page_num + 1} ({width}x{height})")

                except Exception as e:
                    logger.error(f"Error converting page {page_num + 1}: {e}")
                    continue

            pdf_document.close()
            logger.info(f"Successfully converted {len(pages)} pages to images")
            return pages

        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []

    def _get_from_db_cache(self, document_id: str, max_pages: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve PDF cache data from database if it exists and is not expired.

        Args:
            document_id: Document ID
            max_pages: Maximum number of pages

        Returns:
            Cached data or None if not found/expired
        """
        try:
            # Find cache record for this document and max_pages
            stmt = select(PDFCache).where(
                PDFCache.document_id == document_id,
                PDFCache.max_pages == max_pages
            )
            cache_record = self.db.exec(stmt).first()

            if not cache_record:
                return None

            # Check if cache is expired
            current_time = datetime.now(timezone.utc)
            # Ensure expires_at is timezone-aware for comparison
            expires_at = cache_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if current_time > expires_at:
                logger.debug(f"Cache expired for document {document_id}")
                # Delete expired cache record
                self.db.delete(cache_record)
                self.db.commit()
                return None

            logger.debug(f"Cache hit for document {document_id}")
            return json.loads(cache_record.pages_data)

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error reading cache for document {document_id}: {e}")
            return None

    def _save_to_db_cache(self, document_id: str, max_pages: int, data: Dict[str, Any]) -> None:
        """
        Save PDF cache data to database.

        Args:
            document_id: Document ID
            max_pages: Maximum number of pages
            data: Data to cache
        """
        try:
            # Check if cache record already exists
            stmt = select(PDFCache).where(
                PDFCache.document_id == document_id,
                PDFCache.max_pages == max_pages
            )
            existing_cache = self.db.exec(stmt).first()

            if existing_cache:
                # Update existing cache
                existing_cache.total_pages = data.get("total_pages", 0)
                existing_cache.pages_data = json.dumps(data)
                existing_cache.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
                self.db.add(existing_cache)
            else:
                # Create new cache record
                cache_record = PDFCache(
                    document_id=document_id,
                    max_pages=max_pages,
                    total_pages=data.get("total_pages", 0),
                    pages_data=json.dumps(data),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                self.db.add(cache_record)

            self.db.commit()
            logger.debug(f"Cached PDF data for document {document_id}")

        except Exception as e:
            logger.warning(f"Error saving cache for document {document_id}: {e}")
            self.db.rollback()

    def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache records from database.

        Returns:
            Number of records cleaned up
        """
        cleaned_count = 0
        current_time = datetime.now(timezone.utc)

        try:
            # Find all expired cache records
            # Use a more explicit timezone-aware comparison
            stmt = select(PDFCache).where(
                PDFCache.expires_at < current_time
            )
            expired_records = self.db.exec(stmt).all()

            for record in expired_records:
                self.db.delete(record)
                cleaned_count += 1
                logger.debug(f"Cleaned up expired cache record for document {record.document_id}")

            self.db.commit()

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            self.db.rollback()

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired cache records")

        return cleaned_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics from database.

        Returns:
            Dictionary with cache statistics
        """
        try:
            # Count total cache records
            stmt = select(PDFCache)
            cache_records = self.db.exec(stmt).all()
            
            total_records = len(cache_records)
            total_size = sum(len(record.pages_data) for record in cache_records)

            return {
                "total_records": total_records,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "ttl_hours": 24,
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

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

        document = self.db.get(Document, document_id)
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

        document = self.db.get(Document, document_id)
        if not document:
            raise FileNotFoundError(f"Document with ID '{document_id}' not found")

        return self._to_content_response(
            content=document.file_content,
            media_type=document.mime_type,
            filename=document.filename,
            disposition="attachment"
        )
