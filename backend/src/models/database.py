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
    classification: Optional["DocumentClassification"] = Relationship(back_populates="document")
    feedback: List["DocumentFeedback"] = Relationship(back_populates="document")
    pdf_cache: Optional["PDFCache"] = Relationship(back_populates="document")
    ocr_data: List["OCRData"] = Relationship(back_populates="document")

class DocumentClassificationBase(SQLModel):
    """Base classification model"""
    category: str = Field(max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str = Field(max_length=50, default="v1.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentClassification(DocumentClassificationBase, table=True):
    """Document classification table - one-to-one relationship with Document"""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="document.id", unique=True, index=True)
    user_id: Optional[int] = Field(foreign_key="user.id", nullable=True)
    
    # Relationships
    document: Document = Relationship(back_populates="classification")
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

class PDFCacheBase(SQLModel):
    """Base PDF cache model"""
    max_pages: int = Field(ge=0, default=0)  # 0 represents "all pages"
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

class OCRDataBase(SQLModel):
    """Base OCR data model"""
    page_number: int = Field(ge=0)  # Page number (0-indexed)
    full_text: str = Field()  # Complete extracted text for the page
    words_data: str = Field()  # JSON string containing word-level data with bounding boxes
    lines_data: str = Field()  # JSON string containing line-level data with bounding boxes
    confidence_score: float = Field(ge=0.0, le=1.0)  # Average confidence for the page
    total_words: int = Field(ge=0)
    total_lines: int = Field(ge=0)
    original_image_width: Optional[int] = Field(default=None)  # Original image width in pixels
    original_image_height: Optional[int] = Field(default=None)  # Original image height in pixels
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OCRData(OCRDataBase, table=True):
    """OCR data table - stores extracted text and metadata from documents"""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="document.id", index=True)
    
    # Relationships
    document: Document = Relationship(back_populates="ocr_data")


class ProcessingTaskStatus(str, Enum):
    """Processing task status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingTaskBase(SQLModel):
    """Base processing task model"""
    document_id: str = Field(foreign_key="document.id", index=True)
    filename: str = Field()
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    status: ProcessingTaskStatus = Field(default=ProcessingTaskStatus.PENDING, index=True)
    error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProcessingTask(ProcessingTaskBase, table=True):
    """Processing task table - stores document processing tasks for background workers"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    document: Document = Relationship()


class EntityBase(SQLModel):
    """Base entity model"""
    text: str = Field(max_length=500)  # The entity text
    label: str = Field(max_length=50, index=True)  # Entity type (e.g., "PERSON", "LOC", "ORG")
    start: int = Field(ge=0)  # Start character position in the text
    end: int = Field(ge=0)  # End character position in the text
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)  # Optional confidence score
    # Normalized value for entities where applicable (ISO dates, numeric amounts, etc.)
    normalized_value: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Entity(EntityBase, table=True):
    """Named entity extracted from documents"""
    id: Optional[int] = Field(default=None, primary_key=True)
    embedding_metadata_id: int = Field(foreign_key="embeddingmetadata.id", index=True)
    
    # Relationships
    embedding_metadata: "EmbeddingMetadata" = Relationship(back_populates="entities")


class EmbeddingMetadataBase(SQLModel):
    """Base embedding metadata model"""
    document_id: str = Field(foreign_key="document.id", index=True)
    faiss_index: int = Field(ge=0, index=True)  # Position in FAISS index (for linking)
    page_number: int = Field(ge=0)  # Page number (0-indexed)
    text: str = Field()  # The text content that was embedded
    category: str = Field(max_length=100, default="")  # Document classification category
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmbeddingMetadata(EmbeddingMetadataBase, table=True):
    """FAISS embedding metadata table - stores metadata for embeddings indexed in FAISS"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    document: Document = Relationship()
    entities: List["Entity"] = Relationship(back_populates="embedding_metadata")


class CategoryBase(SQLModel):
    """Base category model"""
    name: str = Field(unique=True, index=True, max_length=100)
    description: Optional[str] = Field(max_length=500, nullable=True)
    created_by: Optional[int] = Field(foreign_key="user.id", nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)


class Category(CategoryBase, table=True):
    """Category table - stores document categories for classification"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    creator: Optional[User] = Relationship()
    training_documents: List["CategoryTrainingDocument"] = Relationship(back_populates="category")


class CategoryTrainingDocumentBase(SQLModel):
    """Base category training document model"""
    category_id: int = Field(foreign_key="category.id", index=True)
    document_id: str = Field(foreign_key="document.id", index=True)
    uploaded_by: Optional[int] = Field(foreign_key="user.id", nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CategoryTrainingDocument(CategoryTrainingDocumentBase, table=True):
    """Category training document table - links documents to categories for training"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    category: Category = Relationship(back_populates="training_documents")
    document: Document = Relationship()
    uploader: Optional[User] = Relationship()

# Relationships are now defined directly in the User class