"""
Simple test to verify mock-based testing works.

This test demonstrates that our mock-based approach works
without requiring any real database or external services.
"""

import pytest
from unittest.mock import Mock


class TestSimpleMock:
    """Simple tests to verify mock-based testing works."""
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_mock_database_session(self, mock_db_session):
        """Test that mock database session works."""
        # Arrange
        mock_db_session.get.return_value = None
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        
        # Act
        result = mock_db_session.get("User", 1)
        mock_db_session.add("test_user")
        mock_db_session.commit()
        
        # Assert
        assert result is None
        mock_db_session.get.assert_called_once_with("User", 1)
        mock_db_session.add.assert_called_once_with("test_user")
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_mock_user_fixture(self, mock_user):
        """Test that mock user fixture works."""
        # Assert
        assert mock_user.username == "testuser"
        assert mock_user.email == "test@example.com"
        assert mock_user.user_role == "user"
        assert mock_user.is_active is True
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_mock_document_fixture(self, mock_document):
        """Test that mock document fixture works."""
        # Assert
        assert mock_document.filename == "test_document.pdf"
        assert mock_document.file_size == 1024
        assert mock_document.status == "completed"
        assert mock_document.user_id == 1
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_mock_services(self, mock_auth_service, mock_upload_service, mock_query_service):
        """Test that mock services work."""
        # Arrange
        mock_auth_service.create_user.return_value = Mock()
        mock_upload_service.process_document.return_value = Mock()
        mock_query_service.search_documents.return_value = []
        
        # Act
        auth_result = mock_auth_service.create_user("test_user")
        upload_result = mock_upload_service.process_document("test_doc")
        search_result = mock_query_service.search_documents("test query")
        
        # Assert
        assert auth_result is not None
        assert upload_result is not None
        assert search_result == []
        
        mock_auth_service.create_user.assert_called_once_with("test_user")
        mock_upload_service.process_document.assert_called_once_with("test_doc")
        mock_query_service.search_documents.assert_called_once_with("test query")
    
    @pytest.mark.mock
    @pytest.mark.fast
    def test_mock_external_services(self, mock_ocr_engine, mock_classifier, mock_faiss_index):
        """Test that mock external services work."""
        # Arrange
        mock_ocr_engine.extract_text_from_bytes.return_value = "extracted text"
        mock_classifier.classify.return_value = Mock()
        mock_faiss_index.search.return_value = []
        
        # Act
        ocr_result = mock_ocr_engine.extract_text_from_bytes(b"test content", "pdf")
        classification_result = mock_classifier.classify("test text", "test.pdf")
        search_result = mock_faiss_index.search("test query")
        
        # Assert
        assert ocr_result == "extracted text"
        assert classification_result is not None
        assert search_result == []
        
        mock_ocr_engine.extract_text_from_bytes.assert_called_once_with(b"test content", "pdf")
        mock_classifier.classify.assert_called_once_with("test text", "test.pdf")
        mock_faiss_index.search.assert_called_once_with("test query")
