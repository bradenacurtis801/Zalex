"""Upload service for handling file uploads and processing."""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import config as config
from fastapi import UploadFile
from sqlmodel import Session, select, and_
from src.models.schemas.upload import DocumentClassification, UploadResponse
from src.models.schemas.events import FileStartEvent, FileCompleteEvent
from src.models.database import Document, DocumentClassification as DBDocumentClassification, DocumentStatus
from src.utils.document_processor import DocumentProcessor
from src.utils.file_hasher import calculate_file_hash, get_content_based_filename
import hashlib
from src.event_bus import EventBus, EventType

logger = logging.getLogger(__name__)


def calculate_file_hash_from_content(content: bytes) -> str:
    """Calculate SHA256 hash from file content."""
    return hashlib.sha256(content).hexdigest()


class UploadService:
    """Service for handling file uploads and document processing."""

    def __init__(self, document_processor: DocumentProcessor, db: Session, event_bus: EventBus):
        self.document_processor = document_processor
        self.db = db
        self.event_bus = event_bus


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

        # Extract text and classify document in thread pool to avoid blocking API
        logger.debug(f"Starting document processing for {original_filename}...")
        
        # Run CPU-intensive processing in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            category, confidence = await loop.run_in_executor(
                executor, self._process_document_content, file_content, original_filename
            )
        
        logger.debug(
            f"Final classification result: category={category}, confidence={confidence}"
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

    def _get_existing_classification(
        self, filename: str, original_filename: str
    ) -> Optional[DocumentClassification]:
        """
        Check if a file with the given filename has already been classified.

        Args:
            filename: The content-based filename to look for

        Returns:
            DocumentClassification if found, None otherwise
        """
        try:
            # Search through all categories in the category metadata
            for (
                category,
                documents,
            ) in self.document_processor.category_metadata.items():
                if filename in documents:
                    doc_entry = documents[filename]
                    logger.debug(
                        f"Found existing classification for {filename} in category {category}"
                    )
                    return DocumentClassification(
                        filename=original_filename,
                        category=doc_entry.get("category", category),
                        confidence=doc_entry.get("confidence", 0.0),
                    )

            logger.debug(f"No existing classification found for {filename}")
            return None

        except Exception as e:
            logger.warning(
                f"Error checking for existing classification of {filename}: {e}"
            )
            return None

    async def _save_file(self, file: UploadFile, file_path: str) -> None:
        """
        Save uploaded file to disk.

        Args:
            file: The uploaded file
            file_path: Path where to save the file
        """
        logger.debug(f"Reading file content for {file.filename}...")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.debug(f"File saved successfully. Size: {len(content)} bytes")

    def _extract_text_from_content(self, file_content: bytes, filename: str) -> list:
        """
        Extract text from file content for classification.
        
        Args:
            file_content: The file content as bytes
            filename: The filename for format detection
            
        Returns:
            List of extracted text chunks
        """
        import fitz
        import os
        
        file_extension = os.path.splitext(filename)[1].lower()
        extracted_texts = []
        
        if file_extension == ".pdf":
            try:
                doc = fitz.open(stream=file_content, filetype="pdf")
                for page_num, page in enumerate(doc):
                    # Convert page to image for OCR
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    # Extract text using OCR
                    try:
                        text = self.document_processor.ocr_engine.extract_text_from_bytes(img_data, "png")
                        if text and text.strip():
                            extracted_texts.append(text.strip())
                            logger.debug(f"Extracted text from page {page_num + 1}: {len(text)} characters")
                    except Exception as e:
                        logger.warning(f"OCR failed for page {page_num + 1}: {e}")
                        continue
                
                doc.close()
            except Exception as e:
                logger.error(f"PDF processing failed: {e}")
        else:
            # For image files, process directly
            try:
                image_format = file_extension.lstrip('.')
                if image_format not in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
                    image_format = 'png'
                
                text = self.document_processor.ocr_engine.extract_text_from_bytes(file_content, image_format)
                if text and text.strip():
                    extracted_texts.append(text.strip())
                    logger.debug(f"Extracted text from image: {len(text)} characters")
            except Exception as e:
                logger.error(f"Image processing failed: {e}")
        
        return extracted_texts

    def _process_document_content(self, file_content: bytes, filename: str) -> tuple:
        """
        Process document content (extract text and classify) in a thread pool.
        
        Args:
            file_content: The file content as bytes
            filename: The filename for format detection
            
        Returns:
            Tuple of (category, confidence)
        """
        # Extract text from file content
        extracted_texts = self._extract_text_from_content(file_content, filename)
        
        if not extracted_texts:
            logger.warning(f"No text extracted from {filename}")
            return "other", 0.0
        
        # Classify the document using the extracted text
        try:
            combined_text = " ".join(extracted_texts)
            logger.debug(f"Classifying text with {len(combined_text)} characters...")
            classification_result = self.document_processor.document_classifier.classify(combined_text, filename)
            category = classification_result.category
            confidence = classification_result.confidence
            logger.debug(f"Classification result: {category} ({confidence:.3f})")
            return category, confidence
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "other", 0.0

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
            "upload_session_files": 0
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

            # 5. Finally, delete the Document itself
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

