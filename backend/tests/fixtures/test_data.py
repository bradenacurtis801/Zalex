"""
Test data and sample content for backend tests.

This module provides sample data, documents, and expected outputs
for use across the test suite.
"""

from typing import Dict, List, Any
from pathlib import Path


# Sample user data
SAMPLE_USERS = {
    "regular_user": {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "user_role": "user"
    },
    "admin_user": {
        "username": "testadmin",
        "email": "admin@example.com",
        "full_name": "Test Admin",
        "password": "adminpassword123",
        "user_role": "admin"
    }
}

# Sample document data
SAMPLE_DOCUMENTS = {
    "invoice_pdf": {
        "filename": "sample_invoice.pdf",
        "content_type": "application/pdf",
        "expected_category": "invoice",
        "expected_confidence": 0.95,
        "expected_text": "INVOICE\nInvoice Number: INV-001\nAmount: $100.00"
    },
    "receipt_image": {
        "filename": "sample_receipt.png",
        "content_type": "image/png",
        "expected_category": "receipt",
        "expected_confidence": 0.90,
        "expected_text": "RECEIPT\nStore: Test Store\nTotal: $25.50"
    },
    "contract_pdf": {
        "filename": "sample_contract.pdf",
        "content_type": "application/pdf",
        "expected_category": "contract",
        "expected_confidence": 0.85,
        "expected_text": "CONTRACT\nParties: Company A and Company B\nTerms: 12 months"
    }
}

# Sample search queries and expected results
SAMPLE_QUERIES = {
    "invoice_search": {
        "query": "invoice amount payment",
        "expected_categories": ["invoice"],
        "min_results": 1
    },
    "receipt_search": {
        "query": "receipt store purchase",
        "expected_categories": ["receipt"],
        "min_results": 1
    },
    "contract_search": {
        "query": "contract agreement terms",
        "expected_categories": ["contract"],
        "min_results": 1
    }
}

# Sample classification results
SAMPLE_CLASSIFICATIONS = {
    "invoice": {
        "category": "invoice",
        "confidence": 0.95,
        "method": "mock_classifier"
    },
    "receipt": {
        "category": "receipt",
        "confidence": 0.90,
        "method": "mock_classifier"
    },
    "contract": {
        "category": "contract",
        "confidence": 0.85,
        "method": "mock_classifier"
    },
    "other": {
        "category": "other",
        "confidence": 0.50,
        "method": "mock_classifier"
    }
}

# Sample OCR results
SAMPLE_OCR_RESULTS = {
    "simple_text": {
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
}

# Sample API responses
SAMPLE_API_RESPONSES = {
    "login_success": {
        "session_token": "st_mock_token_123",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "user_role": "user",
            "is_active": True
        }
    },
    "upload_success": {
        "message": "Successfully processed 1 file(s).",
        "classifications": [
            {
                "filename": "sample_invoice.pdf",
                "category": "invoice",
                "confidence": 0.95
            }
        ],
        "already_classified": False
    },
    "search_results": {
        "results": [
            {
                "text": "Sample search result text",
                "source": "sample_document.pdf",
                "page": 1,
                "score": 0.85
            }
        ]
    }
}

# Sample WebSocket messages
SAMPLE_WS_MESSAGES = {
    "handshake": {
        "type": "handshake",
        "data": {
            "token": "st_mock_token_123"
        }
    },
    "handshake_ack": {
        "type": "handshake_ack",
        "data": {
            "user_id": 1,
            "status": "connected"
        }
    },
    "upload_progress": {
        "type": "upload_progress",
        "data": {
            "current_file": 1,
            "total_files": 3,
            "filename": "sample_document.pdf",
            "progress_percent": 33
        }
    }
}

# Test file paths (relative to test data directory)
TEST_FILE_PATHS = {
    "sample_pdf": "sample_documents/sample_invoice.pdf",
    "sample_image": "sample_documents/sample_receipt.png",
    "corrupted_pdf": "sample_documents/corrupted.pdf",
    "large_pdf": "sample_documents/large_document.pdf"
}

def get_sample_user(user_type: str = "regular_user") -> Dict[str, Any]:
    """Get sample user data by type."""
    return SAMPLE_USERS.get(user_type, SAMPLE_USERS["regular_user"])

def get_sample_document(doc_type: str = "invoice_pdf") -> Dict[str, Any]:
    """Get sample document data by type."""
    return SAMPLE_DOCUMENTS.get(doc_type, SAMPLE_DOCUMENTS["invoice_pdf"])

def get_sample_query(query_type: str = "invoice_search") -> Dict[str, Any]:
    """Get sample search query by type."""
    return SAMPLE_QUERIES.get(query_type, SAMPLE_QUERIES["invoice_search"])

def get_sample_classification(category: str = "invoice") -> Dict[str, Any]:
    """Get sample classification result by category."""
    return SAMPLE_CLASSIFICATIONS.get(category, SAMPLE_CLASSIFICATIONS["other"])

def get_sample_ocr_result(result_type: str = "simple_text") -> Dict[str, Any]:
    """Get sample OCR result by type."""
    return SAMPLE_OCR_RESULTS.get(result_type, SAMPLE_OCR_RESULTS["simple_text"])

def get_sample_api_response(response_type: str) -> Dict[str, Any]:
    """Get sample API response by type."""
    return SAMPLE_API_RESPONSES.get(response_type, {})

def get_sample_ws_message(message_type: str) -> Dict[str, Any]:
    """Get sample WebSocket message by type."""
    return SAMPLE_WS_MESSAGES.get(message_type, {})

def get_test_file_path(file_type: str) -> Path:
    """Get test file path by type."""
    return Path(__file__).parent.parent / "data" / TEST_FILE_PATHS.get(file_type, "sample_documents/sample_invoice.pdf")
