"""
Test helper functions and utilities.

This module provides common helper functions used across the test suite
for creating test data, making API requests, and validating responses.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import io


def create_test_file(content: bytes, filename: str, temp_dir: Path) -> Path:
    """Create a test file with given content."""
    file_path = temp_dir / filename
    file_path.write_bytes(content)
    return file_path


def create_test_pdf_content() -> bytes:
    """Create minimal PDF content for testing."""
    # This is a minimal PDF structure - in real tests you'd use a proper PDF library
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"


def create_test_image_content() -> bytes:
    """Create minimal PNG content for testing."""
    # This is a minimal PNG structure - in real tests you'd use a proper image library
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'


def assert_response_success(response, expected_status: int = 200):
    """Assert that a response is successful."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_response_error(response, expected_status: int):
    """Assert that a response is an error."""
    assert response.status_code == expected_status, f"Expected error {expected_status}, got {response.status_code}: {response.text}"


def assert_json_response(response, expected_keys: List[str]):
    """Assert that a JSON response contains expected keys."""
    data = response.json()
    for key in expected_keys:
        assert key in data, f"Expected key '{key}' not found in response: {data}"


def assert_classification_result(classification: Dict[str, Any], expected_category: str, min_confidence: float = 0.0):
    """Assert that a classification result is valid."""
    assert "category" in classification, "Classification missing 'category' field"
    assert "confidence" in classification, "Classification missing 'confidence' field"
    assert classification["category"] == expected_category, f"Expected category '{expected_category}', got '{classification['category']}'"
    assert classification["confidence"] >= min_confidence, f"Confidence {classification['confidence']} below minimum {min_confidence}"


def assert_search_result(search_result: Dict[str, Any]):
    """Assert that a search result is valid."""
    required_fields = ["text", "source", "page", "score"]
    for field in required_fields:
        assert field in search_result, f"Search result missing '{field}' field"
    
    assert isinstance(search_result["text"], str), "Search result 'text' should be string"
    assert isinstance(search_result["source"], str), "Search result 'source' should be string"
    assert isinstance(search_result["page"], int), "Search result 'page' should be integer"
    assert isinstance(search_result["score"], (int, float)), "Search result 'score' should be number"


def create_multipart_file_data(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create multipart file data for testing uploads."""
    return {
        "files": [
            ("files", (file_info["filename"], file_info["content"], file_info["content_type"]))
            for file_info in files
        ]
    }


def extract_error_message(response) -> str:
    """Extract error message from API response."""
    try:
        data = response.json()
        return data.get("detail", "Unknown error")
    except:
        return response.text


def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
    """Wait for a condition to be true with timeout."""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    
    return False


def create_mock_upload_file(filename: str, content: bytes, content_type: str = "application/octet-stream"):
    """Create a mock upload file for testing."""
    from unittest.mock import Mock
    
    mock_file = Mock()
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.read = Mock(return_value=content)
    mock_file.size = len(content)
    
    return mock_file
