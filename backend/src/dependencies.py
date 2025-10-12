"""Dependency injection functions for FastAPI routes."""

from src.services.query_service import QueryService
from src.services.upload_service import UploadService


def get_query_service() -> QueryService:
    """Dependency injection for QueryService."""
    return QueryService()


def get_upload_service() -> UploadService:
    """Dependency injection for UploadService."""
    return UploadService()
