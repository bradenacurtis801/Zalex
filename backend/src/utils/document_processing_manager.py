"""
Document processing service for managing document processing queue and workers.
Delegates actual processing to DocumentProcessor.

Data Flow:
1. OCR Engine returns: OCRResult (raw OCR output with words, lines, text)
2. Service wraps it in: OCRPage (OCRResult + page metadata like page_number, image dimensions)
3. Service saves to DB as: OCRData (database model with serialized JSON)
4. API returns: PageOCRDataResponse (API response schema for frontend)
"""

import asyncio
import logging
import queue
import threading
from typing import Any, Dict, List, Optional

from src.models.database import (
    DocumentStatus,
    ProcessingTaskStatus
)
import config as config
from lib.ocr import OCREngine
from src.ml.classification.base_classifier import DocumentClassifier
from src.ml.faiss.embeddings import EmbeddingsIndex
from src.ml.ner.base_ner import NERModel
from src.event_bus import EventBus, EventType
from src.models.schemas.events import FileStartEvent, FileCompleteEvent
from src.utils.document_processor import DocumentProcessor
from src.models.shared import OCRPage, ProcessingTask
from src.repositories.document_repository import DocumentRepository
from src.repositories.document_classification_repository import DocumentClassificationRepository
from src.repositories.ocr_data_repository import OCRDataRepository
from src.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)


class DocumentProcessManager:
    """Service for processing documents (OCR extraction and classification)."""

    def __init__(
        self,
        ocr_engine: OCREngine,
        document_classifier: DocumentClassifier,
        document_repo: DocumentRepository,
        classification_repo: DocumentClassificationRepository,
        ocr_data_repo: OCRDataRepository,
        task_repo: TaskRepository,
        ner_model: NERModel,
        event_bus: EventBus,
        embeddings_index: EmbeddingsIndex,
        process_workers: int = 1,
    ):
        self.ocr_engine = ocr_engine
        self.document_classifier = document_classifier
        self.document_repo = document_repo
        self.classification_repo = classification_repo
        self.ocr_data_repo = ocr_data_repo
        self.task_repo = task_repo
        self.embeddings_index = embeddings_index
        self.ner_model = ner_model
        self.event_bus = event_bus
        self.worker_queue = queue.Queue()
        
        # Worker thread infrastructure
        self.process_workers_count = process_workers
        self.process_workers: list[threading.Thread] = []
        self.is_running = False

    async def start(self) -> None:
        """
        Start the worker threads and load pending tasks from database.
        """
        if self.is_running:
            logger.warning("Document processing service is already running")
            return
        
        # Load pending tasks from database
        await self._load_pending_tasks()
        
        self.is_running = True
        
        # Start process workers
        logger.info(f"Starting {self.process_workers_count} worker thread(s)")
        for i in range(self.process_workers_count):
            worker = threading.Thread(
                target=self._process_worker,
                args=(f"worker-{i+1}",),
                daemon=True
            )
            worker.start()
            self.process_workers.append(worker)
        
        logger.info("Document processing service workers started")

    async def stop(self) -> None:
        """Stop the worker threads."""
        if not self.is_running:
            return
        
        logger.info("Stopping document processing service workers...")
        self.is_running = False
        
        # Wait for all workers to finish
        for worker in self.process_workers:
            worker.join(timeout=5.0)  # Wait up to 5 seconds for each worker
        
        self.process_workers.clear()
        logger.info("Document processing service workers stopped")

    def check_and_submit(
        self, 
        document_id: str, 
        filename: str, 
        file_content: bytes, 
        user_id: Optional[int]
    ) -> bool:
        """
        Synchronously check if document is already classified. If yes, publish event and return False.
        If no, create DB task, add to worker queue and return True.
        
        Args:
            document_id: Document ID (file hash)
            filename: Document filename
            file_content: Document file content bytes
            user_id: User ID who uploaded the document
            
        Returns:
            True if task was added to queue (needs processing), False if already classified
        """
        logger.info(f"Checking classification status for {document_id} ({filename})")
        
        try:
            # Check if document has been classified
            existing_classification = self.classification_repo.get_by_document_id(document_id)
            
            if existing_classification:
                # Document is already classified - publish event and return (no DB task needed)
                logger.info(
                    f"Document {filename} already classified as {existing_classification.category} "
                    f"(confidence: {existing_classification.confidence:.3f}) - publishing event"
                )
                
                if user_id:
                    event = FileCompleteEvent(
                        user_id=user_id,
                        current_file=1,
                        total_files=1,
                        filename=filename,
                        progress_percent=100,
                        classification={
                            "category": existing_classification.category,
                            "confidence": existing_classification.confidence
                        },
                        was_cached=True
                    )
                    # Publish synchronously (this is a sync method)
                    self.event_bus.publish(EventType.UPLOAD_PROGRESS, event.dict(), source="DocumentProcessingService")
                
                return False  # Already classified, no processing needed
            else:
                # Document not classified or low confidence - create DB task and add to worker queue
                logger.info(f"Document {filename} needs processing - creating DB task and adding to worker queue")
                
                # Check if a pending task already exists for this document
                existing_task = self.task_repo.get_pending_by_document_id(document_id)
                
                if existing_task:
                    # Use existing pending task
                    logger.debug(f"Found existing pending task {existing_task.id} for document {document_id}, reusing it")
                    db_task = existing_task
                else:
                    # Create new task
                    db_task = self.task_repo.create(
                        document_id=document_id,
                        filename=filename,
                        user_id=user_id,
                        status=ProcessingTaskStatus.PENDING
                    )
                
                # Create in-memory task
                task = ProcessingTask(
                    document_id=document_id,
                    filename=filename,
                    file_content=file_content,
                    user_id=user_id,
                    db_task_id=db_task.id
                )
                
                # Add to worker queue
                self.worker_queue.put(task)
                return True  # Added to queue for processing
        
        except Exception as e:
            logger.error(f"Error checking classification for document {document_id}: {e}", exc_info=True)
            # On error, still create task and add to queue to ensure processing happens
            try:
                # Check if a pending task already exists
                existing_task = self.task_repo.get_pending_by_document_id(document_id)
                
                if existing_task:
                    db_task = existing_task
                else:
                    db_task = self.task_repo.create(
                        document_id=document_id,
                        filename=filename,
                        user_id=user_id,
                        status=ProcessingTaskStatus.PENDING
                    )
                
                task = ProcessingTask(
                    document_id=document_id,
                    filename=filename,
                    file_content=file_content,
                    user_id=user_id,
                    db_task_id=db_task.id
                )
                self.worker_queue.put(task)
            except Exception as db_error:
                logger.error(f"Error creating DB task on error: {db_error}", exc_info=True)
            return True

    async def _load_pending_tasks(self) -> None:
        """Load pending tasks from database and add them to the worker queue."""
        try:
            # Reset any tasks stuck in PROCESSING status (from previous crash/restart)
            stuck_tasks = self.task_repo.get_all_processing()
            
            if stuck_tasks:
                logger.info(f"Found {len(stuck_tasks)} task(s) stuck in PROCESSING status, resetting to PENDING")
                self.task_repo.reset_processing_to_pending(stuck_tasks)
                logger.info(f"Reset {len(stuck_tasks)} stuck task(s) to PENDING")
            
            # Load all pending tasks (including the ones we just reset)
            pending_tasks = self.task_repo.get_all_pending()
            
            if pending_tasks:
                logger.info(f"Loading {len(pending_tasks)} pending task(s) from database")
                
                for db_task in pending_tasks:
                    # Get document to retrieve file content
                    document = self.document_repo.get_by_id(db_task.document_id)
                    if not document:
                        logger.warning(f"Document {db_task.document_id} not found for task {db_task.id}, marking as failed")
                        self.task_repo.update_status(
                            db_task, 
                            ProcessingTaskStatus.FAILED, 
                            "Document not found"
                        )
                        continue
                    
                    # Check if already classified, otherwise add to queue
                    self.check_and_submit(
                        document_id=db_task.document_id,
                        filename=db_task.filename,
                        file_content=document.file_content,
                        user_id=db_task.user_id
                    )
                    logger.debug(f"Loaded pending task {db_task.id} for document {db_task.document_id}")
                
                logger.info(f"Successfully loaded {len(pending_tasks)} pending task(s)")
            else:
                logger.debug("No pending tasks found in database")
        
        except Exception as e:
            logger.error(f"Error loading pending tasks from database: {e}", exc_info=True)

    def _update_task_status(
        self, 
        task: ProcessingTask, 
        status: ProcessingTaskStatus, 
        error: Optional[str] = None
    ) -> None:
        """
        Update task status in database.
        
        Args:
            task: The processing task
            status: New status
            error: Error message if failed
        """
        if not task.db_task_id:
            logger.warning(f"Task {task.document_id} has no db_task_id, cannot update status")
            return
        
        try:
            db_task = self.task_repo.get_by_id(task.db_task_id)
            if db_task:
                self.task_repo.update_status(db_task, status, error)
                logger.debug(f"Updated task {task.db_task_id} status to {status.value}")
        except Exception as e:
            logger.error(f"Error updating task status in database: {e}", exc_info=True)

    def _process_worker(self, worker_name: str) -> None:
        """
        Worker thread for processing documents - performs OCR and classification.
        
        Args:
            worker_name: Name identifier for this worker
        """
        logger.info(f"{worker_name} started")
        
        while self.is_running:
            try:
                # Get task from worker queue with timeout
                try:
                    task = self.worker_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                logger.info(f"{worker_name} processing task for document {task.document_id}")
                
                # Update status to PROCESSING in database
                self._update_task_status(task, ProcessingTaskStatus.PROCESSING)
                
                try:
                    # Process the task (OCR + classification) - run async function in thread
                    asyncio.run(self.process_document_task(task))
                    
                    # Fallback: If task still exists and is PROCESSING, mark as completed
                    # (process_document_task should have already called _mark_completed, but this is a safety check)
                    db_task = self.task_repo.get_by_id(task.db_task_id) if task.db_task_id else None
                    if db_task and db_task.status == ProcessingTaskStatus.PROCESSING:
                        # Ensure document is marked as completed
                        document = self.document_repo.get_by_id(task.document_id)
                        if document and document.status != DocumentStatus.COMPLETED:
                            self.document_repo.update_status(document, DocumentStatus.COMPLETED)

                        # Mark task as completed
                        try:
                            self.task_repo.update_status(db_task, ProcessingTaskStatus.COMPLETED, None)
                            logger.debug(f"Marked task {task.db_task_id} as completed (fallback cleanup)")
                        except Exception as e:
                            logger.warning(f"Failed to mark task {task.db_task_id} as completed in fallback: {e}")
                    
                    logger.info(f"{worker_name} completed task for document {task.document_id}")
                
                except Exception as e:
                    logger.error(
                        f"{worker_name} failed to process task for document {task.document_id}: {e}",
                        exc_info=True
                    )
                    self._update_task_status(task, ProcessingTaskStatus.FAILED, str(e))
                
                finally:
                    self.worker_queue.task_done()
            
            except Exception as e:
                logger.error(f"{worker_name} encountered an error: {e}", exc_info=True)
        
        logger.info(f"{worker_name} stopped")

    async def process_document_task(self, task: ProcessingTask) -> None:
        """
        Process a document task by delegating to DocumentProcessor.
        Handles event publishing and error handling.
        
        Args:
            task: The processing task
        """
        logger.info(f"Starting document processing for {task.document_id} ({task.filename})")
        
        # Publish file start event
        if task.user_id:
            event = FileStartEvent(
                user_id=task.user_id,
                current_file=1,
                total_files=1,
                filename=task.filename,
                progress_percent=0
            )
            await self.event_bus.publish_async(
                EventType.UPLOAD_PROGRESS, event.dict(), source="DocumentProcessingService"
            )
        
        try:
            # ========== STEP 1: OCR ==========
            logger.info(f"[Step 1/2] Starting OCR extraction for {task.filename}")
            pages = self._extract_text_from_content(
                task.file_content, task.filename, task.document_id
            )
            
            if not pages:
                raise Exception("No text extracted from document")
            
            logger.info(f"[Step 1/2] OCR complete: extracted {len(pages)} pages")
            
            # Save OCR data to database
            self._save_ocr_data(task.document_id, pages)
            
            # ========== STEP 2: Text Processing ==========
            # Create processor instance (pure text processing, no DB, no OCR)
            # Pass database session for storing FAISS metadata
            processor = DocumentProcessor(
                document_classifier=self.document_classifier,
                ner_model=self.ner_model,
                embeddings_index=self.embeddings_index,
                db=self.task_repo.db,
            )
            
            # Process the pages (returns ProcessingResult)
            # Processor handles classification, NER, and FAISS indexing per page
            result = processor.process(
                pages=pages,
                filename=task.filename,
                document_id=task.document_id,
            )
            
            # Save classification results to database
            self._save_classification_results(
                document_id=task.document_id,
                category=result.category,
                confidence=result.confidence,
                user_id=task.user_id,
                entities=result.entities,
            )
            
            # Update document and task status
            self._mark_completed(task.document_id, task.db_task_id)
            
            # Publish file completion event
            if task.user_id:
                event = FileCompleteEvent(
                    user_id=task.user_id,
                    current_file=1,
                    total_files=1,
                    filename=task.filename,
                    progress_percent=100,
                    classification={
                        "category": result.category,
                        "confidence": result.confidence,
                    },
                    was_cached=False,
                )
                await self.event_bus.publish_async(
                    EventType.UPLOAD_PROGRESS, event.dict(), source="DocumentProcessingService"
                )
        
        except Exception as e:
            # Mark as failed in database
            self._mark_failed(task.document_id, task.db_task_id, str(e))
            raise

    def _extract_text_from_content(
        self, file_content: bytes, filename: str, document_id: str
    ) -> List[OCRPage]:
        """
        Extract text from file content using OCR.
        Returns OCR data for each page.

        Args:
            file_content: The file content as bytes
            filename: The filename for format detection
            document_id: Document ID for storing OCR data

        Returns:
            List of OCRPage objects (intermediate processing structure)
        """
        import os
        import json
        from lib.utils.pdf_helper import PDFHelper

        file_extension = os.path.splitext(filename)[1].lower()
        pages = []

        if file_extension == ".pdf":
            try:
                # Use PDFHelper to extract pages as raw bytes for OCR
                for pdf_page in PDFHelper.extract_pages_as_bytes(file_content, dpi_scale=1.0):
                    # Extract text using OCR with detailed data
                    try:
                        ocr_result = self.ocr_engine.extract_text_from_bytes(
                            pdf_page.image_bytes, "png"
                        )
                        if ocr_result and ocr_result.text.strip():
                            pages.append(
                                OCRPage(
                                    page_number=pdf_page.page_number,  # Already 0-indexed
                                    text=ocr_result.text.strip(),
                                    ocr_result=ocr_result,
                                    image_width=pdf_page.width,
                                    image_height=pdf_page.height,
                                )
                            )
                            logger.debug(
                                f"Extracted text from page {pdf_page.page_number + 1}: "
                                f"{len(ocr_result.text)} characters"
                            )
                    except Exception as e:
                        logger.warning(f"OCR failed for page {pdf_page.page_number + 1}: {e}")
                        continue
            except Exception as e:
                logger.error(f"PDF processing failed: {e}")
        else:
            # For image files, process directly (treat as page 0)
            # File type already validated at API layer, so we can map directly
            try:
                # Map file extension to OCR format (validation ensures these are safe)
                # PNG is the universal fallback - PIL can auto-detect, but format helps EasyOCR
                extension_to_format = {
                    ".jpg": "jpg",
                    ".jpeg": "jpeg",
                    ".png": "png",
                    ".webp": "webp",
                }
                # Use mapped format or default to PNG (universal fallback supported by all OCR engines)
                image_format = extension_to_format.get(file_extension, "png")

                ocr_result = self.ocr_engine.extract_text_from_bytes(file_content, image_format)
                if ocr_result and ocr_result.text.strip():
                    pages.append(
                        OCRPage(
                            page_number=0,  # Single image file = page 0
                            text=ocr_result.text.strip(),
                            ocr_result=ocr_result,
                        )
                    )
                    logger.debug(f"Extracted text from image: {len(ocr_result.text)} characters")
            except Exception as e:
                logger.error(f"Image processing failed: {e}")

        return pages

    def _save_ocr_data(self, document_id: str, pages: List[OCRPage]) -> None:
        """
        Save OCR data for all pages to database.
        Converts OCRPage (processing structure) to OCRData (database model).

        Args:
            document_id: Document ID
            pages: List of OCRPage objects (intermediate processing structure)
        """
        import json

        for page in pages:
            self.ocr_data_repo.create(
                document_id=document_id,
                page_number=page.page_number,
                full_text=page.text,
                words_data=json.dumps(page.ocr_result.words_to_dict()),
                lines_data=json.dumps(page.ocr_result.lines_to_dict()),
                confidence_score=self._calculate_average_confidence_from_ocr_result(page.ocr_result),
                total_words=page.ocr_result.total_words,
                total_lines=page.ocr_result.total_lines,
                original_image_width=page.image_width,
                original_image_height=page.image_height,
            )

    def _calculate_average_confidence_from_ocr_result(self, ocr_result) -> float:
        """Calculate average confidence score from OCRResult."""
        if not ocr_result.words:
            return 0.0

        total_confidence = sum(word.confidence for word in ocr_result.words)
        return total_confidence / len(ocr_result.words) / 100.0  # Convert to 0-1 range

    def _save_classification_results(
        self,
        document_id: str,
        category: str,
        confidence: float,
        user_id: Optional[int],
        entities: List[Dict[str, Any]],
    ) -> None:
        """
        Save classification results to database.

        Args:
            document_id: Document ID
            category: Final category
            confidence: Classification confidence
            user_id: User ID
            entities: Extracted entities
        """
        # Create or update classification record (one-to-one)
        self.classification_repo.create_or_update(
            document_id=document_id,
            category=category,
            confidence=confidence,
            user_id=user_id,
        )

        # Store entities in classification details if needed
        # Note: This could be extended to store entities in a separate table
        if entities:
            logger.debug(f"Extracted entities: {entities}")

    def _mark_completed(self, document_id: str, db_task_id: Optional[int]) -> None:
        """
        Mark document and task as completed.

        Args:
            document_id: Document ID
            db_task_id: Database task ID
        """
        # Update document status
        document = self.document_repo.get_by_id(document_id)
        if document:
            self.document_repo.update_status(document, DocumentStatus.COMPLETED)

        # Update task status to completed
        if db_task_id:
            db_task = self.task_repo.get_by_id(db_task_id)
            if db_task:
                try:
                    self.task_repo.update_status(db_task, ProcessingTaskStatus.COMPLETED, None)
                    logger.debug(f"Marked task {db_task_id} as completed for document {document_id}")
                except Exception as e:
                    # Log error but don't fail - task status update is not critical
                    logger.warning(f"Failed to mark task {db_task_id} as completed: {e}")

        logger.info(f"Marked document {document_id} as completed (task {db_task_id} marked as completed)")

    def _mark_failed(
        self, document_id: str, db_task_id: Optional[int], error: str
    ) -> None:
        """
        Mark document and task as failed.

        Args:
            document_id: Document ID
            db_task_id: Database task ID
            error: Error message
        """
        try:
            # Update document status
            document = self.document_repo.get_by_id(document_id)
            if document:
                self.document_repo.update_status(document, DocumentStatus.FAILED)

            # Update task status to failed
            if db_task_id:
                db_task = self.task_repo.get_by_id(db_task_id)
                if db_task:
                    self.task_repo.update_status(db_task, ProcessingTaskStatus.FAILED, error)
        except Exception as db_error:
            logger.error(f"Error updating document/task status: {db_error}")

