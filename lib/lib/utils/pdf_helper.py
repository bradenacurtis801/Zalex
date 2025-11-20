"""Helper utilities for PDF processing."""

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional, Tuple, Union, TYPE_CHECKING

import fitz  # PyMuPDF
from PIL import Image

if TYPE_CHECKING:
    from fitz import Document

logger = logging.getLogger(__name__)


@dataclass
class PDFPage:
    """Represents a single PDF page as an image."""
    page_number: int
    image_base64: str
    width: int
    height: int
    text: str  # Native text extracted from the page


@dataclass
class PDFPageBytes:
    """Represents a single PDF page as raw image bytes (for OCR processing)."""
    page_number: int
    image_bytes: bytes
    width: int
    height: int
    text: str  # Native text extracted from the page


class PDFHelper:
    """Static helper class for PDF operations."""

    @staticmethod
    def get_page_count(pdf_content: Union[bytes, str, Path]) -> int:
        """
        Get the total number of pages in a PDF.
        
        Args:
            pdf_content: PDF file content as bytes, or path to PDF file (str or Path)
        
        Returns:
            Total number of pages
        """
        pdf_document: "Document"
        try:
            # Handle both bytes and file path
            if isinstance(pdf_content, (str, Path)):
                # Open from file path
                pdf_document = fitz.open(str(pdf_content))
            else:
                # Open from bytes
                pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            return pdf_document.page_count
        finally:
            if pdf_document:
                pdf_document.close()

    @staticmethod
    def extract_pages(
        pdf_content: Union[bytes, str, Path],
        dpi_scale: float = 2.0
    ) -> Generator[PDFPage, None, None]:
        """
        Extract pages from PDF content as images.
        
        Args:
            pdf_content: PDF file content as bytes, or path to PDF file (str or Path)
            dpi_scale: Scale factor for image quality (default: 2.0 for 2x zoom)
        
        Yields:
            PDFPage objects with page_number, image_base64, width, and height
        """
        pdf_document: "Document"
        try:
            # Handle both bytes and file path
            if isinstance(pdf_content, (str, Path)):
                # Open from file path
                pdf_document = fitz.open(str(pdf_content))
            else:
                # Open from bytes
                pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            total_pages = pdf_document.page_count
            
            logger.info(f"Extracting {total_pages} pages from PDF")

            for page_num in range(total_pages):
                try:
                    # Get the page
                    page = pdf_document[page_num]

                    # Convert to image with specified DPI scale for quality
                    mat = fitz.Matrix(dpi_scale, dpi_scale)
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

                    # Extract native text from the page
                    page_text = page.get_text()

                    yield PDFPage(
                        page_number=page_num,  # 0-based page numbers
                        image_base64=img_base64,
                        width=width,
                        height=height,
                        text=page_text
                    )

                    logger.debug(f"Extracted page {page_num} ({width}x{height})")

                except Exception as e:
                    logger.error(f"Error extracting page {page_num}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error opening PDF: {e}")
            raise
        finally:
            if pdf_document:
                pdf_document.close()

    @staticmethod
    def extract_pages_as_bytes(
        pdf_content: Union[bytes, str, Path],
        dpi_scale: float = 1.0
    ) -> Generator[PDFPageBytes, None, None]:
        """
        Extract pages from PDF content as raw image bytes (for OCR processing).
        
        Args:
            pdf_content: PDF file content as bytes, or path to PDF file (str or Path)
            dpi_scale: Scale factor for image quality (default: 1.0 for OCR, can be lower than display)
        
        Yields:
            PDFPageBytes objects with page_number, image_bytes, width, and height
        """
        pdf_document: "Document"
        try:
            # Handle both bytes and file path
            if isinstance(pdf_content, (str, Path)):
                # Open from file path
                pdf_document = fitz.open(str(pdf_content))
            else:
                # Open from bytes
                pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            total_pages = pdf_document.page_count
            
            logger.debug(f"Extracting {total_pages} pages as bytes from PDF")

            for page_num in range(total_pages):
                try:
                    # Get the page
                    page = pdf_document[page_num]

                    # Convert to image with specified DPI scale
                    mat = fitz.Matrix(dpi_scale, dpi_scale)
                    pix = page.get_pixmap(matrix=mat)

                    # Get image dimensions
                    width = pix.width
                    height = pix.height

                    # Get raw image bytes (PNG format)
                    image_bytes = pix.tobytes("png")

                    # Extract native text from the page
                    page_text = page.get_text()

                    yield PDFPageBytes(
                        page_number=page_num,  # 0-based for OCR processing
                        image_bytes=image_bytes,
                        width=width,
                        height=height,
                        text=page_text
                    )

                    logger.debug(f"Extracted page {page_num} as bytes ({width}x{height})")

                except Exception as e:
                    logger.error(f"Error extracting page {page_num} as bytes: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error opening PDF: {e}")
            raise
        finally:
            if pdf_document:
                pdf_document.close()

