"""
Mock implementations of repositories for testing.

This module provides in-memory mock implementations of all repositories
that can be used for unit testing without requiring a database connection.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import json

from src.models.database import (
    Document,
    DocumentStatus,
    DocumentClassification,
    DocumentFeedback,
    PDFCache,
    OCRData,
    EmbeddingMetadata,
    Entity,
    Category,
    CategoryTrainingDocument,
    ProcessingTask,
    ProcessingTaskStatus,
)


class MockCategoryRepository:
    """Mock CategoryRepository for testing."""
    
    def __init__(self):
        self._categories: Dict[int, Category] = {}
        self._categories_by_name: Dict[str, Category] = {}
        self._training_documents: Dict[int, List[CategoryTrainingDocument]] = {}
        self._next_id = 1
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """Get a category by name."""
        return self._categories_by_name.get(name)
    
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """Get a category by ID."""
        return self._categories.get(category_id)
    
    def get_all(self) -> List[Category]:
        """Get all active categories."""
        return [cat for cat in self._categories.values() if cat.is_active]
    
    def create(
        self,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Category:
        """Create a new category."""
        category = Category(
            id=self._next_id,
            name=name,
            description=description,
            created_by=created_by,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._categories[self._next_id] = category
        self._categories_by_name[name] = category
        self._training_documents[self._next_id] = []
        self._next_id += 1
        return category
    
    def add_training_document(
        self,
        category_id: int,
        document_id: str,
        uploaded_by: Optional[int] = None,
    ) -> CategoryTrainingDocument:
        """Add a training document to a category."""
        if category_id not in self._training_documents:
            self._training_documents[category_id] = []
        
        training_doc = CategoryTrainingDocument(
            id=len(self._training_documents[category_id]) + 1,
            category_id=category_id,
            document_id=document_id,
            uploaded_by=uploaded_by,
            created_at=datetime.now(timezone.utc),
        )
        self._training_documents[category_id].append(training_doc)
        return training_doc
    
    def get_training_documents(self, category_id: int) -> List[CategoryTrainingDocument]:
        """Get all training documents for a category."""
        return self._training_documents.get(category_id, [])


class MockDocumentRepository:
    """Mock DocumentRepository for testing."""
    
    def __init__(self):
        self._documents: Dict[str, Document] = {}
    
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self._documents.get(document_id)
    
    def exists(self, document_id: str) -> bool:
        """Check if a document exists."""
        return document_id in self._documents
    
    def create(
        self,
        document_id: str,
        filename: str,
        file_size: int,
        mime_type: str,
        user_id: int,
        status: DocumentStatus = DocumentStatus.PENDING,
    ) -> Document:
        """Create a new document."""
        document = Document(
            id=document_id,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            status=status,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._documents[document_id] = document
        return document
    
    def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
    ) -> Optional[Document]:
        """Update document status."""
        if document_id not in self._documents:
            return None
        self._documents[document_id].status = status
        self._documents[document_id].updated_at = datetime.now(timezone.utc)
        return self._documents[document_id]
    
    def get_by_user_id(self, user_id: int) -> List[Document]:
        """Get all documents for a user."""
        return [doc for doc in self._documents.values() if doc.user_id == user_id]
    
    def delete(self, document_id: str) -> bool:
        """Delete a document."""
        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False


class MockDocumentClassificationRepository:
    """Mock DocumentClassificationRepository for testing."""
    
    def __init__(self):
        self._classifications: Dict[str, DocumentClassification] = {}
    
    def create_or_update(
        self,
        document_id: str,
        category: str,
        confidence: float,
        user_id: Optional[int] = None,
    ) -> DocumentClassification:
        """Create or update a classification."""
        classification = DocumentClassification(
            document_id=document_id,
            category=category,
            confidence=confidence,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._classifications[document_id] = classification
        return classification
    
    def get_by_document_id(self, document_id: str) -> Optional[DocumentClassification]:
        """Get classification by document ID."""
        return self._classifications.get(document_id)
    
    def get_by_category(self, category: str) -> List[DocumentClassification]:
        """Get all classifications for a category."""
        return [
            cls for cls in self._classifications.values()
            if cls.category == category
        ]
    
    def delete(self, document_id: str) -> bool:
        """Delete a classification."""
        if document_id in self._classifications:
            del self._classifications[document_id]
            return True
        return False


class MockTaskRepository:
    """Mock TaskRepository for testing."""
    
    def __init__(self):
        self._tasks: Dict[int, ProcessingTask] = {}
        self._next_id = 1
    
    def get_by_id(self, task_id: int) -> Optional[ProcessingTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_pending_by_document_id(self, document_id: str) -> Optional[ProcessingTask]:
        """Get pending task for a document."""
        for task in self._tasks.values():
            if (task.document_id == document_id and 
                task.status == ProcessingTaskStatus.PENDING):
                return task
        return None
    
    def get_all_pending(self) -> List[ProcessingTask]:
        """Get all pending tasks."""
        return [
            task for task in self._tasks.values()
            if task.status == ProcessingTaskStatus.PENDING
        ]
    
    def get_all_processing(self) -> List[ProcessingTask]:
        """Get all processing tasks."""
        return [
            task for task in self._tasks.values()
            if task.status == ProcessingTaskStatus.PROCESSING
        ]
    
    def create(
        self,
        document_id: str,
        task_type: str,
        status: ProcessingTaskStatus = ProcessingTaskStatus.PENDING,
    ) -> ProcessingTask:
        """Create a new task."""
        task = ProcessingTask(
            id=self._next_id,
            document_id=document_id,
            task_type=task_type,
            status=status,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task
    
    def update_status(
        self,
        task_id: int,
        status: ProcessingTaskStatus,
    ) -> Optional[ProcessingTask]:
        """Update task status."""
        if task_id not in self._tasks:
            return None
        self._tasks[task_id].status = status
        self._tasks[task_id].updated_at = datetime.now(timezone.utc)
        return self._tasks[task_id]
    
    def delete(self, task_id: int) -> bool:
        """Delete a task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all tasks for a document."""
        count = 0
        tasks_to_delete = [
            task_id for task_id, task in self._tasks.items()
            if task.document_id == document_id
        ]
        for task_id in tasks_to_delete:
            del self._tasks[task_id]
            count += 1
        return count


class MockMetadataRepository:
    """Mock MetadataRepository for testing."""
    
    def __init__(self):
        self._metadata: List[EmbeddingMetadata] = []
        self._entities: Dict[int, List[Entity]] = {}
        self._next_metadata_id = 1
        self._next_entity_id = 1
    
    def append(
        self,
        document_id: str,
        faiss_index: int,
        page_number: int,
        text: str,
        category: str = "",
        entities: List[Dict[str, Any]] = None,
    ) -> None:
        """Append metadata."""
        metadata = EmbeddingMetadata(
            id=self._next_metadata_id,
            document_id=document_id,
            faiss_index=faiss_index,
            page_number=page_number,
            text=text,
            category=category,
            created_at=datetime.now(timezone.utc),
        )
        self._metadata.append(metadata)
        
        if entities:
            entity_list = []
            for entity_data in entities:
                entity = Entity(
                    id=self._next_entity_id,
                    metadata_id=self._next_metadata_id,
                    entity_type=entity_data.get("type", ""),
                    entity_text=entity_data.get("text", ""),
                    start_char=entity_data.get("start_char", 0),
                    end_char=entity_data.get("end_char", 0),
                    confidence=entity_data.get("confidence", 0.0),
                )
                entity_list.append(entity)
                self._next_entity_id += 1
            self._entities[self._next_metadata_id] = entity_list
        
        self._next_metadata_id += 1
    
    def get_by_document_id(self, document_id: str) -> List[EmbeddingMetadata]:
        """Get metadata by document ID."""
        return [
            meta for meta in self._metadata
            if meta.document_id == document_id
        ]
    
    def get_entities_by_metadata_id(self, metadata_id: int) -> List[Entity]:
        """Get entities for a metadata record."""
        return self._entities.get(metadata_id, [])
    
    def clear(self) -> None:
        """Clear all metadata."""
        self._metadata.clear()
        self._entities.clear()


class MockPDFCacheRepository:
    """Mock PDFCacheRepository for testing."""
    
    def __init__(self):
        self._cache: Dict[str, PDFCache] = {}
    
    def get_by_document_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get cached PDF data for a document."""
        cache_key = f"{document_id}_0"  # max_pages=0 for all pages
        cache_record = self._cache.get(cache_key)
        
        if not cache_record:
            return None
        
        # Check expiration
        current_time = datetime.now(timezone.utc)
        if cache_record.expires_at < current_time:
            del self._cache[cache_key]
            return None
        
        return json.loads(cache_record.cache_data)
    
    def create_or_update(
        self,
        document_id: str,
        cache_data: Dict[str, Any],
        max_pages: int = 0,
        ttl_hours: int = 24,
    ) -> PDFCache:
        """Create or update cache."""
        cache_key = f"{document_id}_{max_pages}"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        
        cache_record = PDFCache(
            id=len(self._cache) + 1,
            document_id=document_id,
            max_pages=max_pages,
            cache_data=json.dumps(cache_data),
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._cache[cache_key] = cache_record
        return cache_record
    
    def delete_by_document_id(self, document_id: str) -> int:
        """Delete cache for a document."""
        count = 0
        keys_to_delete = [
            key for key in self._cache.keys()
            if key.startswith(f"{document_id}_")
        ]
        for key in keys_to_delete:
            del self._cache[key]
            count += 1
        return count


class MockOCRDataRepository:
    """Mock OCRDataRepository for testing."""
    
    def __init__(self):
        self._ocr_data: Dict[tuple, OCRData] = {}  # (document_id, page_number) -> OCRData
    
    def create(
        self,
        document_id: str,
        page_number: int,
        full_text: str,
        words_data: str,
        lines_data: str,
        confidence_score: float,
        total_words: int,
        total_lines: int,
        original_image_width: Optional[int] = None,
        original_image_height: Optional[int] = None,
    ) -> OCRData:
        """Create OCR data."""
        key = (document_id, page_number)
        ocr_data = OCRData(
            id=len(self._ocr_data) + 1,
            document_id=document_id,
            page_number=page_number,
            full_text=full_text,
            words_data=words_data,
            lines_data=lines_data,
            confidence_score=confidence_score,
            total_words=total_words,
            total_lines=total_lines,
            original_image_width=original_image_width,
            original_image_height=original_image_height,
            created_at=datetime.now(timezone.utc),
        )
        self._ocr_data[key] = ocr_data
        return ocr_data
    
    def get_by_document_id(self, document_id: str) -> List[OCRData]:
        """Get OCR data for a document."""
        return [
            ocr for key, ocr in self._ocr_data.items()
            if key[0] == document_id
        ]
    
    def get_by_document_and_page(
        self,
        document_id: str,
        page_number: int,
    ) -> Optional[OCRData]:
        """Get OCR data for a specific page."""
        key = (document_id, page_number)
        return self._ocr_data.get(key)
    
    def delete_by_document_id(self, document_id: str) -> int:
        """Delete OCR data for a document."""
        count = 0
        keys_to_delete = [
            key for key in self._ocr_data.keys()
            if key[0] == document_id
        ]
        for key in keys_to_delete:
            del self._ocr_data[key]
            count += 1
        return count


class MockDocumentFeedbackRepository:
    """Mock DocumentFeedbackRepository for testing."""
    
    def __init__(self):
        self._feedback: Dict[int, DocumentFeedback] = {}
        self._next_id = 1
    
    def create(
        self,
        document_id: str,
        feedback_type: str,
        suggested_category: Optional[str] = None,
        comment: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> DocumentFeedback:
        """Create feedback."""
        feedback = DocumentFeedback(
            id=self._next_id,
            document_id=document_id,
            feedback_type=feedback_type,
            suggested_category=suggested_category,
            comment=comment,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
        self._feedback[self._next_id] = feedback
        self._next_id += 1
        return feedback
    
    def get_by_document_id(self, document_id: str) -> List[DocumentFeedback]:
        """Get feedback for a document."""
        return [
            fb for fb in self._feedback.values()
            if fb.document_id == document_id
        ]
    
    def get_by_user_id(self, user_id: int) -> List[DocumentFeedback]:
        """Get feedback by a user."""
        return [
            fb for fb in self._feedback.values()
            if fb.user_id == user_id
        ]
    
    def get_by_id(self, feedback_id: int) -> Optional[DocumentFeedback]:
        """Get feedback by ID."""
        return self._feedback.get(feedback_id)

