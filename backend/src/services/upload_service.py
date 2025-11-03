"""Upload service for handling file uploads and processing."""

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlmodel import Session, select, and_
from src.models.schemas.upload import DocumentClassification, UploadResponse
from src.models.schemas.events import FileStartEvent, FileCompleteEvent
from src.models.database import (
    Document, 
    DocumentClassification as DBDocumentClassification, 
    DocumentFeedback, 
    PDFCache, 
    UploadSessionFile, 
    DocumentStatus,
    OCRData
)
from src.ocr import OCREngine
from src.utils.file_hasher import calculate_file_hash, get_content_based_filename
import hashlib
from src.event_bus import EventBus, EventType
from src.ml.classification.base_classifier import DocumentClassifier
from src.ml.faiss.embeddings import EmbeddingsIndex
import config as config

logger = logging.getLogger(__name__)


def calculate_file_hash_from_content(content: bytes) -> str:
    """Calculate SHA256 hash from file content."""
    return hashlib.sha256(content).hexdigest()


class UploadService:
    """Service for handling file uploads and document processing."""

    def __init__(
        self, 
        db: Session, 
        event_bus: EventBus, 
        ocr_engine: OCREngine, 
        document_classifier: DocumentClassifier,
        embeddings_index: Optional[EmbeddingsIndex] = None
    ):
        self.db = db
        self.event_bus = event_bus
        self.ocr_engine = ocr_engine
        self.document_classifier = document_classifier
        self.embeddings_index = embeddings_index

    async def process_upload(self, files: List[UploadFile], user_id: Optional[int] = None) -> UploadResponse:
        """
        Process uploaded files and initiate document processing.

        Args:
            files: List of uploaded files
            user_id: User ID for document ownership and progress updates

        Returns:
            UploadResponse with processing results
        """
        logger.info(f"Processing upload request with {len(files)} file(s)")
        logger.debug(f"File names: {[f.filename for f in files]}")

        if not files or files[0].filename == "":
            logger.debug("No files provided or empty filename")
            raise ValueError("No selected files")

        # Process all files - if any fail, the whole operation fails
        classifications = []
        already_classified_count = 0

        for i, file in enumerate(files):
            # Send progress update via event bus
            if user_id:
                event = FileStartEvent(
                    user_id=user_id,
                    current_file=i + 1,
                    total_files=len(files),
                    filename=file.filename,
                    progress_percent=int((i / len(files)) * 100)
                )
                await self.event_bus.publish_async(EventType.UPLOAD_PROGRESS, event.dict(), source="UploadService")
            
            logger.debug(f"Processing file {i+1}/{len(files)}: {file.filename}")
            classification, was_already_classified = await self._process_single_file(
                file, user_id
            )
            if classification:
                classifications.append(classification)
                if was_already_classified:
                    already_classified_count += 1
            
            # Send file completion update via event bus
            if user_id:
                event = FileCompleteEvent(
                    user_id=user_id,
                    current_file=i + 1,
                    total_files=len(files),
                    filename=file.filename,
                    progress_percent=int(((i + 1) / len(files)) * 100),
                    classification={
                        "category": classification.category if classification else "unknown",
                        "confidence": classification.confidence if classification else 0.0
                    } if classification else None,
                    was_cached=was_already_classified
                )
                await self.event_bus.publish_async(EventType.UPLOAD_PROGRESS, event.dict(), source="UploadService")
            
            logger.debug(f"Successfully processed {file.filename}")

        # Generate appropriate message based on whether files were already classified
        if already_classified_count > 0:
            if already_classified_count == len(files):
                message = f"All {len(files)} file(s) were already classified and returned from cache."
            else:
                message = f"Successfully processed {len(files)} file(s). {already_classified_count} were already classified."
        else:
            message = f"Successfully processed {len(files)} file(s)."

        logger.info(
            f"Upload processing complete. All {len(files)} files processed successfully. "
            f"{already_classified_count} were already classified."
        )
        logger.debug(f"Final message: {message}")

        return UploadResponse(
            message=message,
            classifications=classifications,
            already_classified=already_classified_count > 0,
        )

    async def _process_single_file(
        self, file: UploadFile, user_id: Optional[int] = None
    ) -> tuple[DocumentClassification, bool]:
        """
        Process a single uploaded file and store in database.

        Args:
            file: The uploaded file
            user_id: User ID for document ownership

        Returns:
            DocumentClassification: Classification result for the document

        Raises:
            DocumentProcessingException: If document processing fails
        """
        original_filename = file.filename
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        mime_type = file.content_type or "application/octet-stream"
        
        # Calculate content hash
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            file_hash = await loop.run_in_executor(
                executor, calculate_file_hash_from_content, file_content
            )
        if not file_hash:
            raise Exception(f"Failed to calculate hash for {original_filename}")

        # Check if document already exists in database
        existing_document = self.db.exec(
            select(Document).where(Document.id == file_hash)
        ).first()
        
        if existing_document:
            logger.info(f"Document with same content already exists: {file_hash}")
            
            # Check if it has been classified
            existing_classification = self.db.exec(
                select(DBDocumentClassification)
                .where(DBDocumentClassification.document_id == file_hash)
                .order_by(DBDocumentClassification.created_at.desc())
                .limit(1)
            ).first()
            
            if existing_classification:
                # Check if cached classification meets confidence threshold
                if existing_classification.confidence >= config.CLASSIFIER_CONFIDENCE_THRESHOLD:
                    logger.info(
                        f"Document {original_filename} already classified as {existing_classification.category} "
                        f"(confidence: {existing_classification.confidence:.3f}) - returning cached result"
                    )
                    return DocumentClassification(
                        filename=original_filename,
                        category=existing_classification.category,
                        confidence=existing_classification.confidence
                    ), True
                else:
                    # Cached classification below threshold - re-classify
                    logger.info(
                        f"Document {original_filename} has cached classification with low confidence "
                        f"({existing_classification.confidence:.3f} < {config.CLASSIFIER_CONFIDENCE_THRESHOLD}) - re-classifying"
                    )
                    # Use existing document for re-classification
                    document = existing_document
            else:
                # Document exists but not classified yet - use existing document
                logger.info(f"Document {original_filename} exists but not classified yet - processing")
                document = existing_document
        else:
            # Create new document record
            document = Document(
                id=file_hash,
                filename=original_filename,
                file_content=file_content,
                file_size=file_size,
                mime_type=mime_type,
                user_id=user_id,
                status=DocumentStatus.PROCESSING
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Created document record for {original_filename} with hash {file_hash}")

        # Process document page by page with confidence threshold
        logger.debug(f"Starting document processing for {original_filename}...")
        
        loop = asyncio.get_event_loop()
        
        # Extract all pages first (this needs to complete before parallel processing)
        with ThreadPoolExecutor() as executor:
            extracted_texts, page_numbers = await loop.run_in_executor(
                executor, self._extract_text_from_content, file_content, original_filename, file_hash
            )
        
        # Prepare page data for processing
        all_page_data = [
            (text.strip(), page_num)
            for text, page_num in zip(extracted_texts, page_numbers)
            if text and text.strip()
        ]
        
        logger.debug(f"Extracted {len(all_page_data)} pages for processing")
        
        # Run classification and FAISS indexing in parallel threads
        logger.info(
            f"Starting parallel processing: classification (until threshold met) and "
            f"FAISS indexing (all {len(all_page_data)} pages)"
        )
        
        classification_task = asyncio.create_task(
            self._classify_pages_until_threshold(all_page_data, original_filename, loop)
        )
        faiss_task = asyncio.create_task(
            self._index_all_pages_faiss(all_page_data, file_hash, original_filename, loop)
        )
        
        # Wait for classification (needed for database storage)
        # FAISS indexing runs in parallel and will complete independently
        category, confidence, accepted_page_number = await classification_task
        
        # Wait for FAISS indexing to complete (don't block on errors)
        try:
            await faiss_task
        except Exception as e:
            logger.warning(f"FAISS indexing completed with errors: {e}")
        
        # If no page met threshold, use "other" category
        if confidence < config.CLASSIFIER_CONFIDENCE_THRESHOLD:
            logger.warning(
                f"No page met confidence threshold ({config.CLASSIFIER_CONFIDENCE_THRESHOLD}). "
                f"Best classification was {category} with {confidence:.3f} confidence from page {accepted_page_number + 1}. "
                f"Using 'other' category instead."
            )
            category = "other"
        
        logger.debug(
            f"Final classification result: {category} (confidence: {confidence:.3f}) "
            f"from page {accepted_page_number + 1}"
        )
        
        # Store classification in database
        # Update document status to completed
        document.status = DocumentStatus.COMPLETED
        document.updated_at = datetime.now(timezone.utc)
        self.db.add(document)
        
        # Create classification record
        classification = DBDocumentClassification(
            document_id=file_hash,
            category=category,
            confidence=confidence,
            model_version="v1.0",
            user_id=user_id
        )
        self.db.add(classification)
        self.db.commit()
        
        logger.info(f"Stored classification for {original_filename}: {category} ({confidence:.3f})")
        
        return (
            DocumentClassification(
                filename=original_filename, category=category, confidence=confidence
            ),
            False,
        )

    async def _classify_pages_until_threshold(
        self, 
        all_page_data: List[tuple], 
        filename: str, 
        loop: asyncio.AbstractEventLoop
    ) -> tuple:
        """
        Classify pages sequentially until confidence threshold is met.
        This runs in a separate async task/thread.
        
        Args:
            all_page_data: List of (text, page_number) tuples
            filename: Filename for context
            loop: Event loop for running in executor
            
        Returns:
            Tuple of (category, confidence, accepted_page_number)
        """
        category = None
        confidence = 0.0
        accepted_page_number = -1
        
        with ThreadPoolExecutor() as executor:
            for page_text, page_num in all_page_data:
                # Check if we've already met the threshold
                if confidence >= config.CLASSIFIER_CONFIDENCE_THRESHOLD:
                    logger.debug(
                        f"Classification threshold already met on page {accepted_page_number + 1}. "
                        f"Skipping remaining {len(all_page_data) - page_num} pages."
                    )
                    break
                
                logger.debug(
                    f"[Classification Thread] Classifying page {page_num + 1} "
                    f"(current confidence: {confidence:.3f} < threshold: {config.CLASSIFIER_CONFIDENCE_THRESHOLD})"
                )
                
                # Classify this page in thread pool
                page_category, page_confidence = await loop.run_in_executor(
                    executor,
                    self._classify_single_page,
                    page_text,
                    filename
                )
                
                logger.debug(
                    f"[Classification Thread] Page {page_num + 1} classification: {page_category} "
                    f"(confidence: {page_confidence:.3f})"
                )
                
                # Update if this page has higher confidence
                if page_confidence > confidence:
                    category = page_category
                    confidence = page_confidence
                    accepted_page_number = page_num
                
                # Check if we've met the threshold
                if confidence >= config.CLASSIFIER_CONFIDENCE_THRESHOLD:
                    logger.info(
                        f"[Classification Thread] Confidence threshold met on page {page_num + 1}: "
                        f"{category} (confidence: {confidence:.3f})"
                    )
                    break
        
        # Fallback to "other" if no classification was found
        if category is None:
            category = "other"
            confidence = 0.0
            logger.warning(
                f"[Classification Thread] No classification found for {filename}, using default: other"
            )
        
        return category, confidence, accepted_page_number
    
    async def _index_all_pages_faiss(
        self,
        all_page_data: List[tuple],
        document_id: str,
        filename: str,
        loop: asyncio.AbstractEventLoop
    ) -> None:
        """
        Index all pages in FAISS index.
        This runs in a separate async task/thread and processes all pages.
        
        Args:
            all_page_data: List of (text, page_number) tuples
            document_id: Document ID (file hash)
            filename: Filename for logging
            loop: Event loop for running in executor
        """
        if not self.embeddings_index or not all_page_data:
            logger.debug("[FAISS Thread] No embeddings index or page data, skipping FAISS indexing")
            return
        
        try:
            logger.debug(f"[FAISS Thread] Starting FAISS indexing for {len(all_page_data)} pages...")
            
            # Separate texts and page numbers
            filtered_texts = [data[0] for data in all_page_data]
            filtered_page_numbers = [data[1] for data in all_page_data]
            
            # Add all text chunks to the index (runs in thread pool to avoid blocking)
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    self.embeddings_index.add,
                    filtered_texts,
                    document_id,
                    filtered_page_numbers
                )
            
            logger.debug(
                f"[FAISS Thread] Added {len(filtered_texts)} page(s) to FAISS index for {filename} "
                f"(document_id: {document_id})"
            )
            
            # Save the index
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    self.embeddings_index.store_embeddings
                )
            
            logger.debug("[FAISS Thread] FAISS index saved to disk")
            
        except Exception as e:
            logger.error(f"[FAISS Thread] Failed to index pages in FAISS: {e}", exc_info=True)
            raise

    def _extract_text_from_content(self, file_content: bytes, filename: str, document_id: str = None) -> tuple:
        """
        Extract text from file content for classification.
        
        Args:
            file_content: The file content as bytes
            filename: The filename for format detection
            document_id: Document ID for storing OCR data (optional)
            
        Returns:
            Tuple of (list of extracted text chunks, list of page numbers)
        """
        import fitz
        import os
        
        file_extension = os.path.splitext(filename)[1].lower()
        extracted_texts = []
        page_numbers = []
        
        if file_extension == ".pdf":
            try:
                doc = fitz.open(stream=file_content, filetype="pdf")
                for page_num, page in enumerate(doc):
                    # Convert page to image for OCR
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    # Extract text using OCR with detailed data
                    try:
                        ocr_result = self.ocr_engine.extract_text_from_bytes(img_data, "png")
                        if ocr_result and ocr_result.get('text', '').strip():
                            # Get image dimensions from the pixmap
                            img_width = pix.width
                            img_height = pix.height
                            
                            # Store detailed OCR data in database if document_id is provided
                            if document_id:
                                ocr_data = OCRData(
                                    document_id=document_id,
                                    page_number=page_num,
                                    full_text=ocr_result.get('text', ''),
                                    words_data=json.dumps(ocr_result.get('words', [])),
                                    lines_data=json.dumps(ocr_result.get('lines', [])),
                                    confidence_score=self._calculate_average_confidence(ocr_result.get('words', [])),
                                    total_words=ocr_result.get('total_words', 0),
                                    total_lines=ocr_result.get('total_lines', 0),
                                    original_image_width=img_width,
                                    original_image_height=img_height
                                )
                                self.db.add(ocr_data)
                            
                            # Add text and page number
                            extracted_texts.append(ocr_result.get('text', '').strip())
                            page_numbers.append(page_num)  # 0-indexed page number
                            logger.debug(f"Extracted text from page {page_num + 1}: {len(ocr_result.get('text', ''))} characters")
                    except Exception as e:
                        logger.warning(f"OCR failed for page {page_num + 1}: {e}")
                        continue
                
                doc.close()
            except Exception as e:
                logger.error(f"PDF processing failed: {e}")
        else:
            # For image files, process directly (treat as page 0)
            try:
                image_format = file_extension.lstrip('.')
                if image_format not in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
                    image_format = 'png'
                
                text = self.ocr_engine.extract_text_from_bytes(file_content, image_format)
                if text and text.strip():
                    extracted_texts.append(text.strip())
                    page_numbers.append(0)  # Single image file = page 0
                    logger.debug(f"Extracted text from image: {len(text)} characters")
            except Exception as e:
                logger.error(f"Image processing failed: {e}")
        
        return extracted_texts, page_numbers

    def _classify_single_page(self, page_text: str, filename: str) -> tuple:
        """
        Classify a single page of text.
        
        Args:
            page_text: Text content from a single page
            filename: The filename for context
            
        Returns:
            Tuple of (category, confidence)
        """
        if not page_text or not page_text.strip():
            logger.warning(f"No text provided for classification of {filename}")
            return "other", 0.0
        
        try:
            logger.debug(f"Classifying page text with {len(page_text)} characters...")
            classification_result = self.document_classifier.classify(page_text.strip(), filename)
            category = classification_result.category
            confidence = classification_result.confidence
            logger.debug(f"Page classification result: {category} ({confidence:.3f})")
            return category, confidence
        except Exception as e:
            logger.error(f"Classification failed for page: {e}")
            return "other", 0.0

    def _classify_extracted_text(self, extracted_texts: list, filename: str) -> tuple:
        """
        Classify document using extracted text (backward compatibility method).
        
        Args:
            extracted_texts: List of extracted text chunks
            filename: The filename for context
            
        Returns:
            Tuple of (category, confidence)
        """
        if not extracted_texts:
            logger.warning(f"No text extracted from {filename}")
            return "other", 0.0
        
        # Classify the document using the extracted text
        try:
            combined_text = " ".join(extracted_texts)
            logger.debug(f"Classifying text with {len(combined_text)} characters...")
            classification_result = self.document_classifier.classify(combined_text, filename)
            category = classification_result.category
            confidence = classification_result.confidence
            logger.debug(f"Classification result: {category} ({confidence:.3f})")
            return category, confidence
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "other", 0.0

    def _process_document_content(self, file_content: bytes, filename: str, file_hash: str) -> tuple:
        """
        Process document content (extract text and classify) in a thread pool.
        This method is kept for backward compatibility but is now split into separate methods.
        
        Args:
            file_content: The file content as bytes
            filename: The filename for format detection
            file_hash: The file hash for OCR data storage
            
        Returns:
            Tuple of (category, confidence)
        """
        # Extract text from file content (returns tuple now)
        extracted_texts, _ = self._extract_text_from_content(file_content, filename, file_hash)
        return self._classify_extracted_text(extracted_texts, filename)

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

        # First, check if document exists
        document = self.db.exec(
            select(Document).where(Document.id == document_id)
        ).first()

        if not document:
            logger.warning(f"Document {document_id} not found")
            raise ValueError(f"Document {document_id} not found")

        deletion_counts = {
            "document": 0,
            "classifications": 0,
            "feedback": 0,
            "pdf_cache": 0,
            "upload_session_files": 0,
            "ocr_data": 0
        }

        try:
            # Delete related records first (foreign key constraints)
            
            # 1. Delete DocumentClassifications
            classifications = self.db.exec(
                select(DBDocumentClassification).where(DBDocumentClassification.document_id == document_id)
            ).all()
            for classification in classifications:
                self.db.delete(classification)
                deletion_counts["classifications"] += 1

            # 2. Delete DocumentFeedback
            feedback_records = self.db.exec(
                select(DocumentFeedback).where(DocumentFeedback.document_id == document_id)
            ).all()
            for feedback in feedback_records:
                self.db.delete(feedback)
                deletion_counts["feedback"] += 1

            # 3. Delete PDFCache
            pdf_cache = self.db.exec(
                select(PDFCache).where(PDFCache.document_id == document_id)
            ).first()
            if pdf_cache:
                self.db.delete(pdf_cache)
                deletion_counts["pdf_cache"] += 1

            # 4. Delete UploadSessionFiles that reference this document
            upload_session_files = self.db.exec(
                select(UploadSessionFile).where(UploadSessionFile.document_id == document_id)
            ).all()
            for session_file in upload_session_files:
                self.db.delete(session_file)
                deletion_counts["upload_session_files"] += 1

            # 5. Delete OCRData
            ocr_data_records = self.db.exec(
                select(OCRData).where(OCRData.document_id == document_id)
            ).all()
            for ocr_data in ocr_data_records:
                self.db.delete(ocr_data)
                deletion_counts["ocr_data"] += 1

            # 6. Finally, delete the Document itself
            self.db.delete(document)
            deletion_counts["document"] += 1

            # Commit all deletions
            self.db.commit()

            logger.info(f"Successfully deleted document {document_id} and {sum(deletion_counts.values())} related records")

            return {
                "success": True,
                "message": f"Document '{document.filename}' and all associated data deleted successfully",
                "deletion_counts": deletion_counts,
                "document_id": document_id
            }

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            self.db.rollback()
            raise Exception(f"Failed to delete document: {str(e)}")

    def _calculate_average_confidence(self, words: List[Dict[str, Any]]) -> float:
        """Calculate average confidence score from words data."""
        if not words:
            return 0.0
        
        total_confidence = sum(word.get('confidence', 0) for word in words)
        return total_confidence / len(words) / 100.0  # Convert to 0-1 range

