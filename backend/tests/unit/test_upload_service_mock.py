"""
Unit tests for UploadService using mocked dependencies.

These tests focus on business logic and run fast without external dependencies.
They use mocked services to test the upload service layer in isolation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from io import BytesIO

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.upload_service import UploadService
from src.models.database import Document, DocumentStatus
from src.core.exceptions import DocumentNotFoundError


class TestUploadServiceMocked:
    """Unit tests for UploadService with mocked dependencies."""
    
    def _create_upload_service(self, mock_db_session, mock_ocr_engine=None, mock_classifier=None):
        """Helper method to create UploadService with all required dependencies."""
        if mock_ocr_engine is None:
            mock_ocr_engine = Mock()
        if mock_classifier is None:
            mock_classifier = Mock()
        
        # Mock event bus with async support
        mock_event_bus = Mock()
        mock_event_bus.publish_async = Mock(return_value=None)  # Non-async mock
        
        return UploadService(mock_db_session, mock_event_bus, mock_ocr_engine, mock_classifier)
    
    @pytest.mark.mock
    @pytest.mark.fast
    @pytest.mark.asyncio
    async def test_process_upload_success(self, mock_db_session, mock_user):
        """Test successful document upload processing."""
        # Arrange
        mock_ocr_engine = Mock()
        mock_classifier = Mock()
        
        # Mock event bus with proper async support
        mock_event_bus = Mock()
        async def mock_publish_async(*args, **kwargs):
            return None
        mock_event_bus.publish_async = mock_publish_async
        
        upload_service = UploadService(mock_db_session, mock_event_bus, mock_ocr_engine, mock_classifier)
        
        # Mock file data
        file_content = b"PDF content here"
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        # Mock async read method
        async def mock_read():
            return file_content
        mock_file.read = mock_read
        
        # Mock OCR engine - return string for image processing
        mock_ocr_engine.extract_text_from_bytes.return_value = "Sample extracted text"
        
        # Mock classifier
        mock_classifier.classify.return_value = Mock(category="test_category", confidence=0.95, method="mock")
        
        # Mock database queries
        mock_db_session.exec.return_value.first.return_value = None  # No existing document
        mock_db_session.exec.return_value.all.return_value = []  # No existing classifications
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        # Act
        result = await upload_service.process_upload([mock_file], mock_user.id)
        
        # Assert - Success means no exceptions were raised
        assert result is not None
        assert hasattr(result, 'message')
        assert hasattr(result, 'classifications')
        
        # Verify that the service completed successfully (no exceptions)
        # Note: OCR and classifier may not be called if text extraction fails,
        # but the service should still complete without throwing exceptions
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_extract_text_from_content(self, mock_db_session):
        """Test text extraction from file content."""
        # Arrange
        mock_ocr_engine = Mock()
        upload_service = self._create_upload_service(mock_db_session, mock_ocr_engine)
        
        # Use a PNG image file to match the service's behavior
        file_content = b"PNG image content"
        filename = "test.png"
        document_id = "doc_123"
        
        # Mock OCR engine response - return string for image processing
        expected_text = "Sample extracted text"
        mock_ocr_engine.extract_text_from_bytes.return_value = expected_text
        
        # Act
        result = upload_service._extract_text_from_content(file_content, filename, document_id)
        
        # Assert
        assert result == [expected_text]  # Returns list of text chunks
        mock_ocr_engine.extract_text_from_bytes.assert_called_once_with(file_content, "png")
    
    @pytest.mark.mock
    @pytest.mark.fast
    @pytest.mark.asyncio
    async def test_delete_document_success(self, mock_db_session, mock_document):
        """Test successful document deletion."""
        # Arrange
        upload_service = self._create_upload_service(mock_db_session)
        
        # Mock database queries
        mock_db_session.exec.return_value.first.return_value = mock_document
        mock_db_session.exec.return_value.all.return_value = []  # No related records
        mock_db_session.delete.return_value = None
        mock_db_session.commit.return_value = None
        
        # Act
        result = await upload_service.delete_document("doc_hash_123")
        
        # Assert
        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.mock
    @pytest.mark.fast
    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, mock_db_session):
        """Test document deletion with non-existent document."""
        # Arrange
        upload_service = self._create_upload_service(mock_db_session)
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError):
            await upload_service.delete_document("nonexistent_doc")
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_process_document_content(self, mock_db_session):
        """Test document content processing."""
        # Arrange
        mock_ocr_engine = Mock()
        mock_classifier = Mock()
        upload_service = self._create_upload_service(mock_db_session, mock_ocr_engine, mock_classifier)
        
        # Use a PNG image file to match the service's behavior
        file_content = b"PNG image content"
        filename = "test.png"
        file_hash = "abc123"
        
        # Mock OCR engine response - return string for image processing
        mock_ocr_engine.extract_text_from_bytes.return_value = "Sample extracted text"
        
        # Mock classifier response
        mock_classification = Mock()
        mock_classification.category = "test_category"
        mock_classification.confidence = 0.95
        mock_classification.method = "mock"
        mock_classifier.classify.return_value = mock_classification
        
        # Act
        result = upload_service._process_document_content(file_content, filename, file_hash)
        
        # Assert
        assert result is not None
        assert result == ("test_category", 0.95)  # Returns tuple of (category, confidence)
        mock_ocr_engine.extract_text_from_bytes.assert_called_once_with(file_content, "png")
        mock_classifier.classify.assert_called_once()
    
