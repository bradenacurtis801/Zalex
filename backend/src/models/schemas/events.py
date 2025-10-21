"""
Pydantic schemas for application events.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UploadProgressEvent(BaseModel):
    """Base model for upload progress events."""
    
    type: str = Field(..., description="Event type: 'file_start' or 'file_complete'")
    user_id: int = Field(..., description="User ID for WebSocket targeting")
    current_file: int = Field(..., description="Current file being processed (1-indexed)")
    total_files: int = Field(..., description="Total number of files in upload batch")
    filename: str = Field(..., description="Name of the file being processed")
    progress_percent: int = Field(..., ge=0, le=100, description="Overall progress percentage")


class FileStartEvent(UploadProgressEvent):
    """Event published when a file starts processing."""
    
    type: str = Field(default="file_start", description="Event type")


class FileCompleteEvent(UploadProgressEvent):
    """Event published when a file completes processing."""
    
    type: str = Field(default="file_complete", description="Event type")
    classification: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Classification result with category and confidence"
    )
    was_cached: bool = Field(
        default=False,
        description="Whether this file was already classified (cached result)"
    )


class UploadSessionEvent(BaseModel):
    """Event for upload session updates."""
    
    user_id: int = Field(..., description="User ID")
    status: str = Field(..., description="Session status")
    progress_percent: int = Field(..., ge=0, le=100, description="Session progress")
    current_file: Optional[str] = Field(default=None, description="Currently processing file")
    total_files: int = Field(..., description="Total files in session")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class DocumentProcessedEvent(BaseModel):
    """Event published when a document is fully processed and stored."""
    
    id: str = Field(..., description="Document ID (file hash)")
    filename: str = Field(..., description="Document filename")
    category: str = Field(..., description="Classified category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    user_id: Optional[int] = Field(default=None, description="User who uploaded the document")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")
    was_cached: bool = Field(default=False, description="Whether result was from cache")


class EventMetadata(BaseModel):
    """Metadata for all events."""
    
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    source: str = Field(default="unknown", description="Source service that published the event")
    event_id: Optional[str] = Field(default=None, description="Unique event identifier")


class EventWrapper(BaseModel):
    """Wrapper for all events with metadata."""
    
    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(..., description="Event data")
    metadata: EventMetadata = Field(default_factory=EventMetadata, description="Event metadata")
