"""PDF processing service for converting PDFs to images."""

import base64
import hashlib
import io
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import config
import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


class PDFService:
    """Service for handling PDF operations with caching."""

    def __init__(self):
        """Initialize the PDF service."""
        self.cache_dir = config.APP_DIR / "pdf_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl_hours = 24  # Cache for 24 hours

    def convert_pdf_to_pages(
        self, filename: str, max_pages: int = 20
    ) -> Dict[str, Any]:
        """
        Convert a PDF file to images and return page information.

        Args:
            filename: Name of the PDF file
            max_pages: Maximum number of pages to convert

        Returns:
            Dictionary with page information and image data

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a PDF
            Exception: If conversion fails
        """
        logger.info(f"Converting PDF to pages: {filename}")

        # Security check - ensure filename doesn't contain path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")

        file_path = os.path.join(config.UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {filename}")

        # Check if it's a PDF
        file_extension = filename.lower().split(".")[-1]
        if file_extension != "pdf":
            raise ValueError(f"File is not a PDF: {filename}")

        try:
            # Check cache first
            cache_key = self._get_cache_key(filename, max_pages)
            cached_data = self._get_from_cache(cache_key)

            if cached_data:
                logger.info(f"Using cached PDF pages for {filename}")
                return cached_data

            # Convert PDF to images in memory
            pages = self._convert_pdf_to_images_in_memory(file_path, max_pages)

            if not pages:
                raise Exception("Failed to convert PDF to images")

            result = {"filename": filename, "total_pages": len(pages), "pages": pages}

            # Cache the result
            self._save_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error converting PDF to pages: {e}")
            raise Exception(f"Failed to convert PDF: {str(e)}")

    def _convert_pdf_to_images_in_memory(
        self, pdf_path: str, max_pages: int
    ) -> List[Dict[str, Any]]:
        """
        Convert PDF pages to images in memory.

        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to convert

        Returns:
            List of page dictionaries with image data
        """
        try:
            # Open the PDF
            pdf_document = fitz.open(pdf_path)
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
                    import base64

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

    def _get_cache_key(self, filename: str, max_pages: int) -> str:
        """
        Generate a cache key for the PDF file and max_pages.

        Args:
            filename: Name of the PDF file (should be content-based)
            max_pages: Maximum number of pages

        Returns:
            Cache key string
        """
        # For content-based filenames, we can use the hash directly
        # Format: {hash}_{original_name}.pdf
        from src.utils.file_hasher import extract_hash_from_filename

        file_hash = extract_hash_from_filename(filename)
        if file_hash:
            # Use the content hash directly since it's unique per content
            key_data = f"{file_hash}_{max_pages}"
            return hashlib.md5(key_data.encode()).hexdigest()
        else:
            # Fallback for non-content-based filenames (legacy)
            file_path = os.path.join(config.UPLOAD_DIR, filename)
            try:
                file_mtime = os.path.getmtime(file_path)
                key_data = f"{filename}_{max_pages}_{file_mtime}"
                return hashlib.md5(key_data.encode()).hexdigest()
            except OSError:
                # Fallback if file doesn't exist
                key_data = f"{filename}_{max_pages}"
                return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache if it exists and is not expired.

        Args:
            cache_key: Cache key to look up

        Returns:
            Cached data or None if not found/expired
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check if cache is expired
            cache_time = cache_data.get("timestamp", 0)
            current_time = time.time()
            if current_time - cache_time > (self.cache_ttl_hours * 3600):
                logger.debug(f"Cache expired for key {cache_key}")
                cache_file.unlink()  # Delete expired cache file
                return None

            logger.debug(f"Cache hit for key {cache_key}")
            return cache_data.get("data")

        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Error reading cache file {cache_file}: {e}")
            # Clean up corrupted cache file
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Save data to cache.

        Args:
            cache_key: Cache key
            data: Data to cache
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            cache_data = {"timestamp": time.time(), "data": data}

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"Cached data for key {cache_key}")

        except OSError as e:
            logger.warning(f"Error saving cache file {cache_file}: {e}")

    def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache files.

        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        current_time = time.time()

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)

                    cache_time = cache_data.get("timestamp", 0)
                    if current_time - cache_time > (self.cache_ttl_hours * 3600):
                        cache_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up expired cache file: {cache_file}")

                except (json.JSONDecodeError, KeyError, OSError):
                    # Clean up corrupted files
                    try:
                        cache_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up corrupted cache file: {cache_file}")
                    except OSError:
                        pass

        except OSError as e:
            logger.error(f"Error during cache cleanup: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired cache files")

        return cleaned_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)

            return {
                "total_files": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_dir": str(self.cache_dir),
                "ttl_hours": self.cache_ttl_hours,
            }
        except OSError as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
