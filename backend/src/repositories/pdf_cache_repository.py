"""Repository for PDF cache data access operations."""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from sqlmodel import Session, select
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from src.models.database import PDFCache

logger = logging.getLogger(__name__)


class PDFCacheRepository:
    """Repository for PDF cache database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    def get_by_document_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve PDF cache data for a document if it exists and is not expired.

        Args:
            document_id: Document ID

        Returns:
            Cached data dictionary or None if not found/expired
        """
        try:
            # Use 0 as a sentinel value to represent "all pages"
            stmt = select(PDFCache).where(
                PDFCache.document_id == document_id,
                PDFCache.max_pages == 0
            )
            cache_record = self._db.exec(stmt).first()

            if not cache_record:
                return None

            # Check if cache is expired
            current_time = datetime.now(timezone.utc)
            expires_at = cache_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if current_time > expires_at:
                logger.debug(f"Cache expired for document {document_id}")
                # Delete expired cache record
                self._db.delete(cache_record)
                self._db.commit()
                return None

            logger.debug(f"Cache hit for document {document_id}")
            return json.loads(cache_record.pages_data)

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error reading cache for document {document_id}: {e}")
            return None

    def upsert(self, document_id: str, data: Dict[str, Any], ttl_hours: int = 24) -> None:
        """
        Upsert (insert or update) PDF cache data.
        Handles race conditions with retry logic.

        Args:
            document_id: Document ID
            data: Data to cache
            ttl_hours: Time to live in hours (default: 24)
        """
        try:
            # Try to find existing cache
            stmt = select(PDFCache).where(
                PDFCache.document_id == document_id,
                PDFCache.max_pages == 0
            )
            existing_cache = self._db.exec(stmt).first()

            if existing_cache:
                # Update existing cache
                existing_cache.total_pages = data.get("total_pages", 0)
                existing_cache.pages_data = json.dumps(data)
                existing_cache.expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
                self._db.add(existing_cache)
            else:
                # Create new cache record
                cache_record = PDFCache(
                    document_id=document_id,
                    max_pages=0,  # Use 0 to represent "all pages"
                    total_pages=data.get("total_pages", 0),
                    pages_data=json.dumps(data),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
                )
                self._db.add(cache_record)

            self._db.commit()
            logger.debug(f"Cached PDF data for document {document_id}")

        except IntegrityError as e:
            # Handle race condition: if UniqueViolation, retry with update
            if isinstance(e.orig, UniqueViolation) or "UniqueViolation" in str(e) or "duplicate key" in str(e).lower():
                logger.debug(f"Cache entry already exists for {document_id}, updating instead")
                self._db.rollback()
                self._update_existing(document_id, data, ttl_hours)
            else:
                logger.warning(f"Error saving cache for document {document_id}: {e}")
                self._db.rollback()
                raise
        except Exception as e:
            logger.warning(f"Error saving cache for document {document_id}: {e}")
            self._db.rollback()
            raise

    def _update_existing(self, document_id: str, data: Dict[str, Any], ttl_hours: int) -> None:
        """
        Update existing cache record (used for retry after UniqueViolation).

        Args:
            document_id: Document ID
            data: Data to cache
            ttl_hours: Time to live in hours
        """
        try:
            stmt = select(PDFCache).where(
                PDFCache.document_id == document_id
            )
            existing_cache = self._db.exec(stmt).first()
            if existing_cache:
                existing_cache.max_pages = 0
                existing_cache.total_pages = data.get("total_pages", 0)
                existing_cache.pages_data = json.dumps(data)
                existing_cache.expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
                self._db.add(existing_cache)
                self._db.commit()
                logger.debug(f"Updated cached PDF data for document {document_id}")
            else:
                logger.warning(f"Cache entry not found after UniqueViolation for {document_id}")
        except Exception as retry_error:
            logger.warning(f"Error updating cache for document {document_id}: {retry_error}")
            self._db.rollback()
            raise

    def delete_expired(self) -> int:
        """
        Delete all expired cache records.

        Returns:
            Number of records deleted
        """
        cleaned_count = 0
        current_time = datetime.now(timezone.utc)

        try:
            stmt = select(PDFCache).where(
                PDFCache.expires_at < current_time
            )
            expired_records = self._db.exec(stmt).all()

            for record in expired_records:
                self._db.delete(record)
                cleaned_count += 1
                logger.debug(f"Cleaned up expired cache record for document {record.document_id}")

            self._db.commit()

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            self._db.rollback()

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired cache records")

        return cleaned_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            stmt = select(PDFCache)
            cache_records = self._db.exec(stmt).all()
            
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

    def delete_by_document_id(self, document_id: str) -> bool:
        """
        Delete cache record for a specific document.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(PDFCache).where(
                PDFCache.document_id == document_id
            )
            cache_record = self._db.exec(stmt).first()
            
            if cache_record:
                self._db.delete(cache_record)
                self._db.commit()
                logger.debug(f"Deleted cache for document {document_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cache for document {document_id}: {e}")
            self._db.rollback()
            return False

