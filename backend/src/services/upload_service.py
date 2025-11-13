"""Upload service for handling file uploads."""

import asyncio
import logging
import hashlib
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from fastapi import UploadFile
from src.models.schemas.upload import UploadResponse
from src.models.database import DocumentStatus
from src.services.document_processing_service import DocumentProcessingService
from src.event_bus import EventBus, EventType
from src.models.schemas.events import FileCompleteEvent
from src.repositories.document_repository import DocumentRepository
from src.repositories.document_classification_repository import DocumentClassificationRepository
from src.repositories.pdf_cache_repository import PDFCacheRepository
from src.repositories.ocr_data_repository import OCRDataRepository
from src.repositories.document_feedback_repository import DocumentFeedbackRepository
from src.repositories.metadata_repository import MetadataRepository
import config as config

logger = logging.getLogger(__name__)


def calculate_file_hash_from_content(content: bytes) -> str:
    """Calculate SHA256 hash from file content."""
    return hashlib.sha256(content).hexdigest()


class UploadService:
    """Service for handling file uploads - saves documents and submits processing tasks."""

    def __init__(
        self, 
        processing_service: DocumentProcessingService,
        document_repo: DocumentRepository,
        classification_repo: DocumentClassificationRepository,
        pdf_cache_repo: PDFCacheRepository,
        ocr_data_repo: OCRDataRepository,
        feedback_repo: DocumentFeedbackRepository,
        metadata_repo: MetadataRepository,
        event_bus: Optional[EventBus] = None,
    ):
        self.processing_service = processing_service
        self.document_repo = document_repo
        self.classification_repo = classification_repo
        self.pdf_cache_repo = pdf_cache_repo
        self.ocr_data_repo = ocr_data_repo
        self.feedback_repo = feedback_repo
        self.metadata_repo = metadata_repo
        self.event_bus = event_bus

    async def process_upload(self, files: List[UploadFile], user_id: Optional[int] = None) -> UploadResponse:
        """
        Process uploaded files - saves documents to DB and submits processing tasks to queue.

        Args:
            files: List of uploaded files
            user_id: User ID for document ownership

        Returns:
            UploadResponse indicating successful upload
        """
        logger.info(f"Processing upload request with {len(files)} file(s)")
        logger.debug(f"File names: {[f.filename for f in files]}")

        if not files or files[0].filename == "":
            logger.debug("No files provided or empty filename")
            raise ValueError("No selected files")

        tasks_submitted = 0

        for file in files:
            logger.debug(f"Processing file: {file.filename}")

            # Read file content first to calculate hash
            file_content = await file.read()
            file_hash = calculate_file_hash_from_content(file_content)
            
            # Reset file pointer so _save_document can read it again
            await file.seek(0)
            
            # Save document and get file content for processing
            needs_processing, file_content = await self._save_document(file, file_hash, user_id)
            
            # Submit processing task if needed
            if needs_processing and file_content:
                # check_and_submit is synchronous - checks if classified, creates DB task if needed, adds to queue
                needs_processing = self.processing_service.check_and_submit(
                    document_id=file_hash,
                    filename=file.filename,
                    file_content=file_content,
                    user_id=user_id
                )
                if needs_processing:
                    tasks_submitted += 1
                    logger.info(f"Submitted processing task for {file.filename}")
                else:
                    logger.info(f"Document {file.filename} already classified, event published")
            
            logger.debug(f"Successfully processed {file.filename}")

        message = f"Successfully uploaded {len(files)} file(s). Processing in background."

        logger.info(f"Upload complete. {len(files)} files saved. {tasks_submitted} submitted for processing.")

        return UploadResponse(
            message=message,
            classifications=None,
            already_classified=False,
        )

    async def _save_document(
        self, file: UploadFile, file_hash: str, user_id: Optional[int] = None
    ) -> tuple[bool, Optional[bytes]]:
        """
        Save document to database.

        Args:
            file: The uploaded file
            user_id: User ID for document ownership

        Returns:
            Tuple of (needs_processing, file_content)
        """
        original_filename = file.filename
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        mime_type = file.content_type or "application/octet-stream"

        # Check if document already exists in database
        existing_document = self.document_repo.get_by_id(file_hash)
        
        if existing_document:
            logger.info(f"Document with same content already exists: {file_hash}")
            # Update status to processing if not already completed
            if existing_document.status != DocumentStatus.COMPLETED:
                self.document_repo.update_status(existing_document, DocumentStatus.PROCESSING)
                return (True, file_content)  # Needs processing
            else:
                # Document already processed - check if it's classified and post to event bus directly
                logger.info(f"Document {original_filename} already processed - checking classification")
                
                # Check if document has a classification
                classification = self.classification_repo.get_latest_by_document_id(file_hash)
            
                if classification and classification.confidence >= config.CLASSIFIER_CONFIDENCE_THRESHOLD:
                    # Document is already classified - post to event bus directly
                    logger.info(
                        f"Document {original_filename} already classified as {classification.category} "
                        f"(confidence: {classification.confidence:.3f}) - posting to event bus"
                    )
                    
                    if self.event_bus and user_id:
                        event = FileCompleteEvent(
                            user_id=user_id,
                            current_file=1,
                            total_files=1,
                            filename=original_filename,
                            progress_percent=100,
                            classification={
                                "category": classification.category,
                                "confidence": classification.confidence
                            },
                            was_cached=True
                        )
                        # Post to event bus asynchronously
                        await self.event_bus.publish_async(
                            EventType.UPLOAD_PROGRESS, 
                            event.dict(), 
                            source="UploadService"
                        )
                    
                    return (False, None)  # No processing needed, event already posted
                else:
                    # Document completed but not classified or low confidence - submit to processing queue
                    logger.info(f"Document {original_filename} completed but needs classification - submitting to processing queue")
                    return (True, file_content)  # Submit task for processing
        else:
            # Create new document record
            self.document_repo.create(
                document_id=file_hash,
                filename=original_filename,
                file_content=file_content,
                file_size=file_size,
                mime_type=mime_type,
                user_id=user_id,
                status=DocumentStatus.PROCESSING
            )
            
            logger.info(f"Created document record for {original_filename} with hash {file_hash}")
            return (True, file_content)  # Needs processing

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
        result = self.document_repo.delete(document_id=document_id)
        return result

