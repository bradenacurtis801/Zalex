"""Dependency injection functions for FastAPI routes."""

from src.services.category_service import CategoryService
from src.services.feedback_service import FeedbackService
from src.services.pdf_service import PDFService
from src.services.query_service import QueryService
from src.services.upload_service import UploadService


def get_query_service() -> QueryService:
    """Dependency injection for QueryService."""
    return QueryService()


def get_upload_service() -> UploadService:
    """Dependency injection for UploadService."""
    return UploadService()


def get_category_service() -> CategoryService:
    """Dependency injection for CategoryService."""
    return CategoryService()


def get_feedback_service() -> FeedbackService:
    """Dependency injection for FeedbackService."""
    return FeedbackService()


def get_pdf_service() -> PDFService:
    """Dependency injection for PDFService."""
    return PDFService()
