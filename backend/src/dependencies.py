"""Dependency injection functions for FastAPI routes."""

import config
from app_state import get_app_state
from fastapi import Depends
from src.services.category_service import CategoryService
from src.services.feedback_service import FeedbackService
from src.services.pdf_service import PDFService
from src.services.query_service import QueryService
from src.services.upload_service import UploadService
from src.utils.document_processor import DocumentProcessor


def get_document_processor() -> DocumentProcessor:
    """Dependency injection for DocumentProcessor."""
    app_state = get_app_state()
    return app_state.document_processor


def get_upload_service(
    document_processor: DocumentProcessor = Depends(get_document_processor),
) -> UploadService:
    """Dependency injection for UploadService."""
    return UploadService(document_processor)


def get_pdf_service() -> PDFService:
    """Dependency injection for PDFService."""
    return PDFService()


def get_document_classifier():
    """Dependency injection for document classifier."""
    app_state = get_app_state()
    return app_state.document_classifier


def get_category_metadata():
    """Dependency injection for category metadata."""
    app_state = get_app_state()
    return app_state.category_metadata


def get_model_path():
    """Dependency injection for model path."""
    return str(config.CLASSIFIER_MODEL_PATH)


def get_index():
    """Dependency injection for FAISS index."""
    app_state = get_app_state()
    return app_state.index


def get_metadata():
    """Dependency injection for metadata."""
    app_state = get_app_state()
    return app_state.metadata


def get_model():
    """Dependency injection for SentenceTransformer model."""
    app_state = get_app_state()
    return app_state.model


def get_category_service(
    document_classifier=Depends(get_document_classifier),
    category_metadata=Depends(get_category_metadata),
) -> CategoryService:
    """Dependency injection for CategoryService."""
    return CategoryService(document_classifier, category_metadata)


def get_feedback_service(
    document_classifier=Depends(get_document_classifier),
    category_metadata=Depends(get_category_metadata),
    model_path=Depends(get_model_path),
) -> FeedbackService:
    """Dependency injection for FeedbackService."""
    return FeedbackService(document_classifier, category_metadata, model_path)


def get_query_service(
    index=Depends(get_index),
    metadata=Depends(get_metadata),
    model=Depends(get_model),
) -> QueryService:
    """Dependency injection for QueryService."""
    return QueryService(index, metadata, model)
