from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import UniqueConstraint, DateTime as sa_DateTime

class UserRole(str, Enum):
    """User role"""
    USER = "user"
    ADMIN = "admin"

class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True, max_length=255)
    full_name: str = Field(max_length=255)
    user_role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str = Field(max_length=255)
    
    # Relationships
    sessions: List["Session"] = Relationship(back_populates="user")
    documents: List["Document"] = Relationship(back_populates="user")

class SessionBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    session_token: str = Field(unique=True, index=True, max_length=255)
    is_revoked: bool = Field(default=False)  # For immediate revocation
    expires_at: datetime = Field()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Session(SessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    user: User = Relationship(back_populates="sessions")

class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UploadSessionStatus(str, Enum):
    """Upload session status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class DocumentBase(SQLModel):
    """Base document model with common fields"""
    filename: str = Field(max_length=500)  # Original filename without modification
    file_content: bytes  # The actual document content (PDF, image, etc.)
    file_size: int = Field(ge=0)  # File size in bytes
    mime_type: str = Field(max_length=100)
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Document(DocumentBase, table=True):
    """Document table - file hash is the primary key"""
    id: str = Field(primary_key=True, max_length=64)  # SHA256 hash as primary key
    user_id: Optional[int] = Field(foreign_key="user.id", nullable=True)  # Optional user association
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="documents")
    classifications: List["DocumentClassification"] = Relationship(back_populates="document")
    feedback: List["DocumentFeedback"] = Relationship(back_populates="document")
    pdf_cache: Optional["PDFCache"] = Relationship(back_populates="document")

class DocumentClassificationBase(SQLModel):
    """Base classification model"""
    category: str = Field(max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str = Field(max_length=50, default="v1.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentClassification(DocumentClassificationBase, table=True):
    """Document classification table"""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="document.id")
    user_id: Optional[int] = Field(foreign_key="user.id", nullable=True)
    
    # Relationships
    document: Document = Relationship(back_populates="classifications")
    user: Optional[User] = Relationship()

class DocumentFeedbackBase(SQLModel):
    """Base feedback model"""
    feedback_type: str = Field(max_length=50)  # "correct", "incorrect", "uncertain"
    suggested_category: Optional[str] = Field(max_length=100, nullable=True)
    comment: Optional[str] = Field(max_length=1000, nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentFeedback(DocumentFeedbackBase, table=True):
    """Document feedback table"""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="document.id")
    user_id: Optional[int] = Field(foreign_key="user.id", nullable=True)
    
    # Relationships
    document: Document = Relationship(back_populates="feedback")
    user: Optional[User] = Relationship()

class UploadSessionBase(SQLModel):
    """Base upload session model"""
    client_id: str = Field(max_length=100, unique=True, index=True)
    status: UploadSessionStatus = Field(default=UploadSessionStatus.ACTIVE)
    total_files: int = Field(ge=0)
    processed_files: int = Field(ge=0, default=0)
    current_file: Optional[str] = Field(max_length=500, nullable=True)
    progress_percent: float = Field(ge=0.0, le=100.0, default=0.0)
    error_message: Optional[str] = Field(max_length=1000, nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24), sa_type=sa_DateTime(timezone=True))

class UploadSession(UploadSessionBase, table=True):
    """Upload session table - tracks user upload progress"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id", nullable=True)
    
    # Relationships
    user: Optional[User] = Relationship()
    files: List["UploadSessionFile"] = Relationship(back_populates="session")

class UploadSessionFileBase(SQLModel):
    """Base upload session file model"""
    filename: str = Field(max_length=500)
    file_size: int = Field(ge=0)
    mime_type: str = Field(max_length=100)
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED)
    error_message: Optional[str] = Field(max_length=1000, nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UploadSessionFile(UploadSessionFileBase, table=True):
    """Upload session file table - tracks individual files in upload session"""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="uploadsession.id")
    file_hash: Optional[str] = Field(max_length=64, nullable=True)  # Set when file is processed
    document_id: Optional[str] = Field(foreign_key="document.id", nullable=True)  # Link to final document
    
    # Relationships
    session: UploadSession = Relationship(back_populates="files")
    document: Optional[Document] = Relationship()

class PDFCacheBase(SQLModel):
    """Base PDF cache model"""
    max_pages: int = Field(ge=1, le=100)
    total_pages: int = Field(ge=0)
    pages_data: str = Field()  # JSON string containing page data
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24), sa_type=sa_DateTime(timezone=True))

class PDFCache(PDFCacheBase, table=True):
    """PDF cache table - stores converted PDF pages"""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="document.id", unique=True, index=True)
    
    # Relationships
    document: Document = Relationship(back_populates="pdf_cache")


# Relationships are now defined directly in the User class