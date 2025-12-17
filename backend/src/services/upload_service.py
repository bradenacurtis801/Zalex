"""Upload service for handling file uploads."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from lib.utils.file_hasher import calculate_file_hash_from_content

import config as config
from src.event_bus import EventBus, EventType
from src.models.database import Document, DocumentClassification, DocumentStatus
from src.models.schemas.events import FileCompleteEvent
from src.models.schemas.upload import UploadResponse
from src.repositories import DataRepository
from src.utils.document_processing_manager import DocumentProcessManager

logger = logging.getLogger(__name__)


class UploadService:
    """Service for handling file uploads - saves documents and submits processing tasks."""

    def __init__(
        self, 
        document_process_manager: DocumentProcessManager,
        data_repo: DataRepository,
        event_bus: EventBus,
    ):
        self._document_process_manager = document_process_manager
        self._data_repo = data_repo
        self._event_bus = event_bus

    async def process_upload(self, files: List[UploadFile], user_id: Optional[int] = None) -> UploadResponse:
        """Process uploaded files - saves documents to DB and submits processing tasks to queue."""
        logger.info(f"Processing upload request with {len(files)} file(s)")
        logger.debug(f"File names: {[f.filename for f in files]}")

        if not files or files[0].filename == "":
            logger.debug("No files provided or empty filename")
            raise ValueError("No selected files")

        tasks_submitted = 0

        for file in files:
            logger.debug(f"Processing file: {file.filename}")

            file_content = await file.read()
            file_hash = calculate_file_hash_from_content(file_content)
            
            # Save document and handle processing/events
            task_submitted = await self._handle_document_upload(
                file, file_hash, file_content, user_id
            )
            
            if task_submitted:
                tasks_submitted += 1
            
            logger.debug(f"Successfully processed {file.filename}")

        message = f"Successfully uploaded {len(files)} file(s). Processing in background."
        logger.info(f"Upload complete. {len(files)} files saved. {tasks_submitted} submitted for processing.")

        return UploadResponse(
            message=message,
            classifications=None,
            already_classified=False,
        )

    async def _handle_document_upload(
        self, 
        file: UploadFile, 
        file_hash: str, 
        file_content: bytes,
        user_id: Optional[int]
    ) -> bool:
        """
        Handle document upload - save to DB and submit for processing if needed.
        
        Returns:
            True if a processing task was submitted, False otherwise
        """
        existing_document = self._data_repo.get_document(file_hash)
        
        if existing_document:
            return await self._handle_existing_document(
                existing_document, file.filename, file_hash, file_content, user_id
            )
        else:
            return await self._handle_new_document(
                file, file_hash, file_content, user_id
            )

    async def _handle_existing_document(
        self,
        document: Document,
        filename: str,
        file_hash: str,
        file_content: bytes,
        user_id: Optional[int]
    ) -> bool:
        """
        Handle an existing document upload.
        
        Returns:
            True if a processing task was submitted, False otherwise
        """
        logger.info(f"Document with same content already exists: {file_hash}")
        
        if document.status != DocumentStatus.COMPLETED:
            # Document exists but not completed - reprocess
            self._data_repo.update_document_status(document, DocumentStatus.PROCESSING)
            return self._submit_for_processing(file_hash, filename, file_content, user_id)
        
        # Document is completed - check classification
        classification = self._data_repo.get_classification_by_document_id(file_hash)
        
        if self._is_classified(classification):
            await self._publish_cached_classification_event(
                filename, classification, user_id
            )
            return False
        else:
            # Completed but needs classification
            logger.info(f"Document {filename} completed but needs classification")
            return self._submit_for_processing(file_hash, filename, file_content, user_id)

    async def _handle_new_document(
        self,
        file: UploadFile,
        file_hash: str,
        file_content: bytes,
        user_id: Optional[int]
    ) -> bool:
        """
        Handle a new document upload.
        
        Returns:
            True if a processing task was submitted, False otherwise
        """
        file_size = len(file_content)
        mime_type = file.content_type or "application/octet-stream"
        
        self._data_repo.create_document(
            document_id=file_hash,
            filename=file.filename,
            file_content=file_content,
            file_size=file_size,
            mime_type=mime_type,
            user_id=user_id,
            status=DocumentStatus.PROCESSING
        )
        
        logger.info(f"Created document record for {file.filename} with hash {file_hash}")
        return self._submit_for_processing(file_hash, file.filename, file_content, user_id)

    def _is_classified(self, classification: Optional[DocumentClassification]) -> bool:
        """Check if a classification exists and meets confidence threshold."""
        return (
            classification is not None 
            and classification.confidence >= config.CLASSIFIER_CONFIDENCE_THRESHOLD
        )

    async def _publish_cached_classification_event(
        self,
        filename: str,
        classification: DocumentClassification,
        user_id: int
    ) -> None:
        """Publish an event for a cached classification."""
        logger.info(
            f"Document {filename} already classified as {classification.category} "
            f"(confidence: {classification.confidence:.3f}) - posting to event bus"
        )
        
        event = FileCompleteEvent(
            user_id=user_id,
            current_file=1,
            total_files=1,
            filename=filename,
            progress_percent=100,
            classification={
                "category": classification.category,
                "confidence": classification.confidence
            },
            was_cached=True
        )
        await self._event_bus.publish_async(
            EventType.UPLOAD_PROGRESS, 
            event.model_dump(), 
            source="UploadService"
        )

    def _submit_for_processing(
        self,
        file_hash: str,
        filename: str,
        file_content: bytes,
        user_id: int
    ) -> bool:
        """
        Submit document for processing.
        
        Returns:
            True if task was submitted, False if already classified
        """
        needs_processing = self._document_process_manager.check_and_submit(
            document_id=file_hash,
            filename=filename,
            file_content=file_content,
            user_id=user_id
        )
        
        if needs_processing:
            logger.info(f"Submitted processing task for {filename}")
        else:
            logger.info(f"Document {filename} already classified, event published")
        
        return needs_processing

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document and all its associated data.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Dict with success message and deletion details

        Raises:
            ValueError: If document not found
            Exception: If deletion fails
        """
        logger.info(f"Starting deletion of document {document_id}")

        # Use the repository method that handles all cascading deletes
        result = self._data_repo.delete_document(document_id=document_id)
        return result

