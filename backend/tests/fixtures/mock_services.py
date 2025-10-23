"""
Mock implementations of external services for testing.

This module provides mock implementations of external services like OCR engines,
ML classifiers, and other dependencies that are difficult to test in isolation.
"""

from typing import Dict, List, Any, Optional
import json
from unittest.mock import Mock


class MockOCREngine:
    """Mock OCR engine for testing."""
    
    def __init__(self):
        self.initialized = True
        self.extraction_count = 0
    
    def initialize(self):
        """Mock initialization."""
        self.initialized = True
    
    def extract_text(self, file_path: str) -> str:
        """Mock text extraction from file path."""
        self.extraction_count += 1
        return f"Mock extracted text from {file_path}"
    
    def extract_text_from_bytes(self, content: bytes, format: str) -> Dict[str, Any]:
        """Mock text extraction from bytes."""
        self.extraction_count += 1
        return {
            "text": f"Mock extracted text from {format} bytes",
            "words": [
                {"text": "Mock", "confidence": 95, "bbox": [0, 0, 10, 10]},
                {"text": "extracted", "confidence": 90, "bbox": [10, 0, 20, 10]},
                {"text": "text", "confidence": 88, "bbox": [20, 0, 30, 10]}
            ],
            "lines": [
                {
                    "text": "Mock extracted text",
                    "confidence": 92,
                    "bbox": [0, 0, 30, 10],
                    "words": [0, 1, 2]
                }
            ],
            "total_words": 3,
            "total_lines": 1
        }


class MockDocumentClassifier:
    """Mock document classifier for testing."""
    
    def __init__(self):
        self.is_initialized = True
        self.classification_count = 0
        self.supported_categories = [
            "invoice", "receipt", "contract", "report", "other"
        ]
    
    def classify(self, text: str, filename: str) -> 'ClassificationResult':
        """Mock document classification."""
        self.classification_count += 1
        
        # Simple mock classification based on text content
        text_lower = text.lower()
        if "invoice" in text_lower or "bill" in text_lower:
            category = "invoice"
            confidence = 0.95
        elif "receipt" in text_lower or "purchase" in text_lower:
            category = "receipt"
            confidence = 0.90
        elif "contract" in text_lower or "agreement" in text_lower:
            category = "contract"
            confidence = 0.85
        elif "report" in text_lower or "analysis" in text_lower:
            category = "report"
            confidence = 0.80
        else:
            category = "other"
            confidence = 0.50
        
        return ClassificationResult(category, confidence, "mock_classifier")
    
    def get_supported_categories(self) -> List[str]:
        """Get list of supported categories."""
        return self.supported_categories.copy()


class ClassificationResult:
    """Mock classification result."""
    
    def __init__(self, category: str, confidence: float, method: str):
        self.category = category
        self.confidence = confidence
        self.method = method


class MockFAISSIndex:
    """Mock FAISS index for testing."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors = []
        self.metadata = []
        self.ntotal = 0
    
    def add(self, vectors):
        """Mock adding vectors to index."""
        import numpy as np
        vectors_array = np.array(vectors)
        self.vectors.extend(vectors_array)
        self.ntotal += len(vectors_array)
    
    def search(self, query_vector, k: int):
        """Mock search in index."""
        import numpy as np
        
        if not self.vectors:
            return np.array([[0.0]]), np.array([[-1]])
        
        # Simple mock search - return random results
        n_results = min(k, len(self.vectors))
        distances = np.random.random((1, n_results))
        indices = np.random.randint(0, len(self.vectors), (1, n_results))
        
        return distances, indices


class MockSentenceTransformer:
    """Mock sentence transformer for testing."""
    
    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name
        self.dimension = 384
    
    def encode(self, texts, convert_to_tensor: bool = False):
        """Mock text encoding."""
        import numpy as np
        
        if isinstance(texts, str):
            texts = [texts]
        
        # Generate random embeddings
        embeddings = np.random.random((len(texts), self.dimension)).astype('float32')
        
        if convert_to_tensor:
            import torch
            return torch.tensor(embeddings)
        
        return embeddings
    
    def get_sentence_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class MockEventBus:
    """Mock event bus for testing."""
    
    def __init__(self):
        self.subscribers = {}
        self.published_events = []
    
    def subscribe_async(self, event_type, handler):
        """Mock async subscription."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def publish_async(self, event_type, data, source=None):
        """Mock async event publishing."""
        event = {
            "type": event_type,
            "data": data,
            "source": source
        }
        self.published_events.append(event)
        
        # Call subscribers if any
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.received_messages = []
        self.connected = False
    
    async def accept(self):
        """Mock WebSocket accept."""
        self.connected = True
    
    async def send_text(self, message: str):
        """Mock sending text message."""
        self.sent_messages.append(message)
    
    async def receive_text(self) -> str:
        """Mock receiving text message."""
        if self.received_messages:
            return self.received_messages.pop(0)
        return '{"type": "ping", "data": {}}'
    
    async def close(self):
        """Mock WebSocket close."""
        self.connected = False


class MockPDFService:
    """Mock PDF service for testing."""
    
    def __init__(self):
        self.cached_pages = {}
        self.cache_stats = {"hits": 0, "misses": 0}
    
    def get_document_content_response(self, document_id: str):
        """Mock document content response."""
        return {
            "content": f"Mock PDF content for {document_id}",
            "content_type": "application/pdf"
        }
    
    def get_document_download_response(self, document_id: str):
        """Mock document download response."""
        return {
            "content": f"Mock PDF download for {document_id}",
            "filename": f"document_{document_id}.pdf",
            "content_type": "application/pdf"
        }
    
    def get_pdf_pages(self, document_id: str, max_pages: int = 20):
        """Mock PDF pages response."""
        pages = []
        for i in range(min(max_pages, 5)):  # Mock 5 pages max
            pages.append({
                "page_number": i + 1,
                "image_data": f"base64_encoded_image_data_for_page_{i+1}",
                "width": 800,
                "height": 600
            })
        
        return {
            "document_id": document_id,
            "total_pages": 5,
            "pages": pages,
            "cached": document_id in self.cached_pages
        }
    
    def get_cache_stats(self):
        """Mock cache statistics."""
        return self.cache_stats
