"""Dependency injection functions for FastAPI routes."""

import config
import logging
from app_state import get_app_state

from fastapi import Depends, File, HTTPException, status, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from typing import Generator, List, Optional, Annotated

from src.services.category_service import CategoryService
from src.services.feedback_service import FeedbackService
from src.services.pdf_service import PDFService
from src.services.query_service import QueryService
from src.services.upload_service import UploadService
from src.services.ocr_service import OCRService
from src.services.document_processing_service import DocumentProcessingService
from src.services.auth_service import AuthService
from src.services.task_service import TaskService
from src.websocket_manager import get_connection_manager
from src.db.connection import get_session
from src.event_bus import event_bus
from src.models.shared import ProcessingTask
from src.models.database import User, UserRole
from src.core.exceptions import UnsupportedFileTypeError
from src.repositories import (
    DocumentRepository,
    PDFCacheRepository,
    MetadataRepository,
    OCRDataRepository,
    DocumentClassificationRepository,
    DocumentFeedbackRepository,
    TaskRepository,
)

# Security scheme
security = HTTPBearer(auto_error=False)  # ← Don't raise error if missing

def get_db() -> Session:
    """Database dependency"""
    return next(get_session())


# ========== Repository Dependencies ==========

def get_document_repository(db: Session = Depends(get_session)) -> DocumentRepository:
    """Dependency injection for DocumentRepository."""
    return DocumentRepository(db)


def get_pdf_cache_repository(db: Session = Depends(get_session)) -> PDFCacheRepository:
    """Dependency injection for PDFCacheRepository."""
    return PDFCacheRepository(db)


def get_metadata_repository(db: Session = Depends(get_session)) -> MetadataRepository:
    """Dependency injection for MetadataRepository."""
    return MetadataRepository(db)


def get_ocr_data_repository(db: Session = Depends(get_session)) -> OCRDataRepository:
    """Dependency injection for OCRDataRepository."""
    return OCRDataRepository(db)


def get_document_classification_repository(
    db: Session = Depends(get_session),
) -> DocumentClassificationRepository:
    """Dependency injection for DocumentClassificationRepository."""
    return DocumentClassificationRepository(db)


def get_document_feedback_repository(db: Session = Depends(get_session)) -> DocumentFeedbackRepository:
    """Dependency injection for DocumentFeedbackRepository."""
    return DocumentFeedbackRepository(db)

def get_task_repository(db: Session = Depends(get_session)) -> TaskRepository:
    """Dependency injection for TaskRepository."""
    return TaskRepository(db)

# ========== Service Dependencies ==========

def get_auth_service(db: Session = Depends(get_session)) -> AuthService:
    return AuthService(db)

def get_embeddings_index():
    """Dependency injection for FAISS embeddings index."""
    app_state = get_app_state()
    return app_state.embeddings_index

def get_document_processing_service():
    """Dependency injection for DocumentProcessingService."""
    app_state = get_app_state()
    if not app_state.document_processing_service:
        raise RuntimeError("Document processing service not initialized")
    return app_state.document_processing_service

def get_upload_service(
    processing_service: DocumentProcessingService = Depends(get_document_processing_service),
    document_repo: DocumentRepository = Depends(get_document_repository),
    classification_repo: DocumentClassificationRepository = Depends(get_document_classification_repository),
    pdf_cache_repo: PDFCacheRepository = Depends(get_pdf_cache_repository),
    ocr_data_repo: OCRDataRepository = Depends(get_ocr_data_repository),
    feedback_repo: DocumentFeedbackRepository = Depends(get_document_feedback_repository),
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> UploadService:
    """Dependency injection for UploadService."""
    return UploadService(
        processing_service=processing_service,
        event_bus=event_bus,
        document_repo=document_repo,
        classification_repo=classification_repo,
        pdf_cache_repo=pdf_cache_repo,
        feedback_repo=feedback_repo,
        ocr_data_repo=ocr_data_repo,
        metadata_repo=metadata_repo,
    )


def get_pdf_service(
    document_repo: DocumentRepository = Depends(get_document_repository),
    classification_repo: DocumentClassificationRepository = Depends(get_document_classification_repository),
    pdf_cache_repo: PDFCacheRepository = Depends(get_pdf_cache_repository),
) -> PDFService:
    """Dependency injection for PDFService."""
    return PDFService(
        document_repo=document_repo,
        classification_repo=classification_repo,
        pdf_cache_repo=pdf_cache_repo,
    )


def get_document_classifier():
    """Dependency injection for document classifier."""
    app_state = get_app_state()
    return app_state.document_classifier


def get_category_service(
    document_classifier=Depends(get_document_classifier),
    classification_repo: DocumentClassificationRepository = Depends(get_document_classification_repository),
) -> CategoryService:
    """Dependency injection for CategoryService."""
    return CategoryService(document_classifier, classification_repo)


def get_feedback_service(
    document_classifier=Depends(get_document_classifier),
    document_repo: DocumentRepository = Depends(get_document_repository),
    classification_repo: DocumentClassificationRepository = Depends(get_document_classification_repository),
) -> FeedbackService:
    """Dependency injection for FeedbackService."""
    return FeedbackService(document_classifier, document_repo, classification_repo)

def get_query_service(
    embeddings_index=Depends(get_embeddings_index),
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> QueryService:
    """Dependency injection for QueryService."""
    return QueryService(embeddings_index, metadata_repo)

def get_ocr_service(
    ocr_data_repo: OCRDataRepository = Depends(get_ocr_data_repository),
) -> OCRService:
    """Get OCR service instance"""
    app_state = get_app_state()
    return OCRService(app_state.ocr_engine, ocr_data_repo)

def get_task_service(
    processing_task_repo: TaskRepository = Depends(get_task_repository),
) -> TaskService:
    """Dependency injection for TaskService."""
    return TaskService(processing_task_repo)

# Simple authentication - only session tokens
async def get_current_user(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_session)
) -> User:
    """
    Get current user from session token.
    In development mode, if no token is provided, returns a default admin user.
    """
    
    # In development mode, allow requests without authentication
    if config.is_development:
        if not bearer_credentials:
            # Return default admin user in dev mode when no token is provided
            admin_user = db.exec(select(User).where(User.username == "admin")).first()
            if admin_user:
                return admin_user
            # If admin doesn't exist, create a mock user for dev
            logger = logging.getLogger(__name__)
            logger.warning("No admin user found in dev mode, creating temporary user")
            # Try to get any user, or create a temporary one
            any_user = db.exec(select(User)).first()
            if any_user:
                return any_user
            # Last resort: return a mock user object
            return User(
                id=1,
                username="dev_user",
                email="dev@scanpro.local",
                full_name="Development User",
                user_role=UserRole.ADMIN,
                is_active=True,
                password_hash=""
            )
        
        # If token is provided in dev mode, still verify it
        token = bearer_credentials.credentials
        user = auth_service.verify_session_token(token)
        if user:
            return user
        # If token is invalid in dev mode, fall back to admin user
        admin_user = db.exec(select(User).where(User.username == "admin")).first()
        if admin_user:
            return admin_user
    
    # Production mode: require authentication
    if not bearer_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = bearer_credentials.credentials
    
    # Verify session token
    user = auth_service.verify_session_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_admin():
    """Require admin role"""
    async def check_admin(current_user: User = Depends(get_current_user)) -> User:
        if current_user.user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    return check_admin
