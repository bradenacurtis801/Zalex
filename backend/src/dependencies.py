"""Dependency injection functions for FastAPI routes."""

import config
from app_state import get_app_state
from fastapi import Depends
from src.services.category_service import CategoryService
from src.services.feedback_service import FeedbackService
from src.services.pdf_service import PDFService
from src.services.query_service import QueryService
from src.services.upload_service import UploadService
from src.services.ocr_service import OCRService
from src.utils.document_processor import DocumentProcessor
from src.websocket_manager import get_connection_manager
from src.db.connection import get_session
from src.event_bus import event_bus
from sqlmodel import Session
from typing import Generator, List, Optional, Annotated
from sqlmodel import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.services.auth_service import AuthService
from src.models.database import User, UserRole

# Security scheme
security = HTTPBearer(auto_error=False)  # ← Don't raise error if missing

def get_db() -> Session:
    """Database dependency"""
    return next(get_session())

def get_auth_service(db: Session = Depends(get_session)) -> AuthService:
    return AuthService(db)

def get_document_processor() -> DocumentProcessor:
    """Dependency injection for DocumentProcessor."""
    app_state = get_app_state()
    return app_state.document_processor

def get_upload_service(
    document_processor: DocumentProcessor = Depends(get_document_processor),
    db: Session = Depends(get_session),
) -> UploadService:
    """Dependency injection for UploadService."""
    return UploadService(document_processor, db, event_bus)


def get_pdf_service(db: Session = Depends(get_session)) -> PDFService:
    """Dependency injection for PDFService."""
    return PDFService(db)


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
    db: Session = Depends(get_session),
) -> CategoryService:
    """Dependency injection for CategoryService."""
    return CategoryService(document_classifier, category_metadata, db)


def get_feedback_service(
    document_classifier=Depends(get_document_classifier),
    category_metadata=Depends(get_category_metadata),
    db: Session = Depends(get_session),
) -> FeedbackService:
    """Dependency injection for FeedbackService."""
    return FeedbackService(document_classifier, category_metadata, db)


def get_query_service(
    index=Depends(get_index),
    metadata=Depends(get_metadata),
    model=Depends(get_model),
) -> QueryService:
    """Dependency injection for QueryService."""
    return QueryService(index, metadata, model)

# Simple authentication - only session tokens
async def get_current_user(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current user from session token"""
    
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

def get_ocr_service(db: Session = Depends(get_session)) -> OCRService:
    """Get OCR service instance"""
    app_state = get_app_state()
    return OCRService(db, app_state.document_processor.ocr_engine)

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
