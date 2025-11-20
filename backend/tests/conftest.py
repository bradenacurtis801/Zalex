"""
Global pytest configuration and fixtures for backend tests.

This file contains shared fixtures and configuration for mock-based testing.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator
import pytest
import pytest_asyncio
from unittest.mock import Mock, MagicMock, patch

# Mock-based testing - No real database needed
# We use mocked database sessions instead of real database connections

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock-based testing fixtures
@pytest.fixture
def mock_db_session():
    """Mock PostgreSQL database session for unit tests.
    
    This fixture provides a mocked database session that simulates
    PostgreSQL behavior without requiring a real database connection.
    Perfect for fast, isolated unit tests.
    """
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.refresh = Mock()
    mock_session.get = Mock()
    mock_session.exec = Mock()
    mock_session.delete = Mock()
    mock_session.rollback = Mock()
    mock_session.query = Mock()
    
    # Mock PostgreSQL-specific behavior
    mock_session.execute = Mock()
    mock_session.scalar = Mock()
    mock_session.scalars = Mock()
    mock_session.merge = Mock()
    
    return mock_session


@pytest.fixture
def mock_user():
    """Mock user object for testing."""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.user_role = "user"
    user.is_active = True
    user.password_hash = "hashed_password"
    user.created_at = "2024-01-01T00:00:00Z"
    user.updated_at = "2024-01-01T00:00:00Z"
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user object for testing."""
    user = Mock()
    user.id = 2
    user.username = "admin"
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.user_role = "admin"
    user.is_active = True
    user.password_hash = "hashed_admin_password"
    user.created_at = "2024-01-01T00:00:00Z"
    user.updated_at = "2024-01-01T00:00:00Z"
    return user


@pytest.fixture
def mock_document():
    """Mock document object for testing."""
    document = Mock()
    document.id = "test_document_hash"
    document.filename = "test_document.pdf"
    document.file_size = 1024
    document.mime_type = "application/pdf"
    document.status = "completed"
    document.user_id = 1
    document.created_at = "2024-01-01T00:00:00Z"
    document.updated_at = "2024-01-01T00:00:00Z"
    return document


@pytest.fixture
def mock_auth_service():
    """Mock auth service for testing."""
    mock = Mock()
    mock.create_user.return_value = Mock()
    mock.authenticate_user.return_value = Mock()
    mock.verify_session_token.return_value = Mock()
    mock.get_user.return_value = Mock()
    return mock


@pytest.fixture
def mock_upload_service():
    """Mock upload service for testing."""
    mock = Mock()
    mock.process_document.return_value = Mock()
    mock.upload_document.return_value = Mock()
    mock.get_document.return_value = Mock()
    return mock


@pytest.fixture
def mock_query_service():
    """Mock query service for testing."""
    mock = Mock()
    mock.search_documents.return_value = []
    mock.get_document.return_value = Mock()
    mock.get_documents_by_category.return_value = []
    return mock


@pytest.fixture
def mock_ocr_engine():
    """Mock OCR engine for testing."""
    mock = Mock()
    mock.extract_text_from_bytes.return_value = "Mock extracted text"
    mock.extract_text.return_value = "Mock extracted text"
    return mock


@pytest.fixture
def mock_classifier():
    """Mock document classifier for testing."""
    mock = Mock()
    mock.classify.return_value = Mock(category="test_category", confidence=0.95, method="mock")
    return mock


@pytest.fixture
def mock_faiss_index():
    """Mock FAISS index for testing."""
    mock = Mock()
    mock.search.return_value = []
    return mock


@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer for testing."""
    mock = Mock()
    mock.encode.return_value = [[0.1, 0.2, 0.3]]
    return mock




# Removed AppState mock - not needed for service-level testing


@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing."""
    from tests.fixtures.mock_services import MockWebSocket
    return MockWebSocket()


@pytest.fixture
def mock_event_bus():
    """Mock event bus for testing."""
    from tests.fixtures.mock_services import MockEventBus
    return MockEventBus()


@pytest.fixture
def mock_pdf_service():
    """Mock PDF service for testing."""
    from tests.fixtures.mock_services import MockPDFService
    return MockPDFService()


# Sample data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user creation data."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "password123",
        "user_role": "user"
    }


@pytest.fixture
def sample_login_data():
    """Sample login data."""
    return {
        "username": "testuser",
        "password": "password123"
    }


@pytest.fixture
def sample_document_data():
    """Sample document data."""
    return {
        "filename": "test_document.pdf",
        "content_type": "application/pdf",
        "file_size": 1024,
        "content": b"PDF content here"
    }


@pytest.fixture
def sample_classification_result():
    """Sample classification result."""
    class MockResult:
        def __init__(self):
            self.category = "invoice"
            self.confidence = 0.95
            self.method = "mock_classifier"
    
    return MockResult()


@pytest.fixture
def sample_ocr_result():
    """Sample OCR result."""
    return {
        "text": "Sample extracted text",
        "words": [
            {"text": "Sample", "confidence": 95, "bbox": [0, 0, 10, 10]},
            {"text": "extracted", "confidence": 90, "bbox": [10, 0, 20, 10]},
            {"text": "text", "confidence": 88, "bbox": [20, 0, 30, 10]}
        ],
        "lines": [
            {
                "text": "Sample extracted text",
                "confidence": 92,
                "bbox": [0, 0, 30, 10],
                "words": [0, 1, 2]
            }
        ],
        "total_words": 3,
        "total_lines": 1
    }


@pytest.fixture
def sample_search_result():
    """Sample search result."""
    return {
        "text": "Sample search result text",
        "source": "test_document.pdf",
        "page": 1,
        "score": 0.85
    }


# Mock patches for external dependencies
@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock external services that shouldn't be called during unit tests."""
    with patch('os.getenv') as mock_getenv:
        
        # Mock environment variables to avoid config loading issues
        def mock_env_get(key, default=None):
            env_vars = {
                'CORS_ORIGINS': '["http://localhost:3000"]',
                'DATABASE_URL': 'postgresql://postgres:password@localhost:5432/app_test',
                'JWT_SECRET_KEY': 'test_secret',
                'DEBUG': '1',
                'NODE_ENV': 'test'
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = mock_env_get
        
        yield {
            'getenv': mock_getenv
        }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for mock-based tests."""
    config.addinivalue_line(
        "markers", "mock: Mock-based unit tests"
    )
    config.addinivalue_line(
        "markers", "fast: Fast-running tests"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests with mocked dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with real database"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "auth: Authentication-related tests"
    )
    config.addinivalue_line(
        "markers", "upload: Upload-related tests"
    )
    config.addinivalue_line(
        "markers", "search: Search-related tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests that should be excluded from quick runs"
    )


# Mock repository fixtures
@pytest.fixture
def mock_category_repository():
    """Mock CategoryRepository for testing."""
    from tests.fixtures.mock_repositories import MockCategoryRepository
    return MockCategoryRepository()


@pytest.fixture
def mock_document_repository():
    """Mock DocumentRepository for testing."""
    from tests.fixtures.mock_repositories import MockDocumentRepository
    return MockDocumentRepository()


@pytest.fixture
def mock_document_classification_repository():
    """Mock DocumentClassificationRepository for testing."""
    from tests.fixtures.mock_repositories import MockDocumentClassificationRepository
    return MockDocumentClassificationRepository()


@pytest.fixture
def mock_task_repository():
    """Mock TaskRepository for testing."""
    from tests.fixtures.mock_repositories import MockTaskRepository
    return MockTaskRepository()


@pytest.fixture
def mock_metadata_repository():
    """Mock MetadataRepository for testing."""
    from tests.fixtures.mock_repositories import MockMetadataRepository
    return MockMetadataRepository()


@pytest.fixture
def mock_pdf_cache_repository():
    """Mock PDFCacheRepository for testing."""
    from tests.fixtures.mock_repositories import MockPDFCacheRepository
    return MockPDFCacheRepository()


@pytest.fixture
def mock_ocr_data_repository():
    """Mock OCRDataRepository for testing."""
    from tests.fixtures.mock_repositories import MockOCRDataRepository
    return MockOCRDataRepository()


@pytest.fixture
def mock_document_feedback_repository():
    """Mock DocumentFeedbackRepository for testing."""
    from tests.fixtures.mock_repositories import MockDocumentFeedbackRepository
    return MockDocumentFeedbackRepository()