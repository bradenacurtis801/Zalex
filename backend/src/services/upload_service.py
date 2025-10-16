"""Upload service for handling file uploads and processing."""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import config as config
from fastapi import UploadFile
from src.models.upload import DocumentClassification, UploadResponse
from src.utils.document_processor import DocumentProcessor
from src.utils.file_hasher import calculate_file_hash, get_content_based_filename
from src.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)


class UploadService:
    """Service for handling file uploads and document processing."""

    def __init__(self, document_processor: DocumentProcessor, connection_manager: ConnectionManager):
        self.document_processor = document_processor
        self.connection_manager = connection_manager


    async def process_upload(self, files: List[UploadFile], client_id: str = None) -> UploadResponse:
        """
        Process uploaded files and initiate document processing.

        Args:
            files: List of uploaded files

        Returns:
            UploadResponse with processing results
        """
        logger.info(f"Processing upload request with {len(files)} file(s)")
        logger.debug(f"File names: {[f.filename for f in files]}")

        if not files or files[0].filename == "":
            logger.debug("No files provided or empty filename")
            raise ValueError("No selected files")

        # Use the injected document processor
        processor = self.document_processor
        logger.debug("Using injected document processor")
        logger.debug(f"Upload directory: {config.UPLOAD_DIR}")

        # Ensure upload directory exists
        self._ensure_upload_directory()

        # Process all files - if any fail, the whole operation fails
        classifications = []
        already_classified_count = 0

        for i, file in enumerate(files):
            # Send progress update
            if client_id and self.connection_manager:
                await self.connection_manager.send_progress(client_id, {
                    "type": "file_start",
                    "current_file": i + 1,
                    "total_files": len(files),
                    "filename": file.filename,
                    "progress_percent": int((i / len(files)) * 100)
                })
            
            logger.debug(f"Processing file {i+1}/{len(files)}: {file.filename}")
            classification, was_already_classified = await self._process_single_file(
                file, processor
            )
            if classification:
                classifications.append(classification)
                if was_already_classified:
                    already_classified_count += 1
            
            # Send file completion update
            if client_id and self.connection_manager:
                await self.connection_manager.send_progress(client_id, {
                    "type": "file_complete",
                    "current_file": i + 1,
                    "total_files": len(files),
                    "filename": file.filename,
                    "progress_percent": int(((i + 1) / len(files)) * 100),
                    "classification": {
                        "category": classification.category if classification else "unknown",
                        "confidence": classification.confidence if classification else 0.0
                    }
                })
            
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

    def _ensure_upload_directory(self) -> None:
        """Ensure the upload directory exists."""
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        logger.debug(f"Upload directory ensured: {config.UPLOAD_DIR}")

    async def _process_single_file(
        self, file: UploadFile, processor
    ) -> tuple[DocumentClassification, bool]:
        """
        Process a single uploaded file.

        Args:
            file: The uploaded file
            processor: Document processor instance

        Returns:
            DocumentClassification: Classification result for the document

        Raises:
            DocumentProcessingException: If document processing fails
        """
        original_filename = file.filename

        # First, save to a temporary location to calculate hash
        temp_file_path = os.path.join(config.UPLOAD_DIR, f"temp_{original_filename}")
        await self._save_file(file, temp_file_path)

        # Calculate content hash - run in thread pool for large files
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            file_hash = await loop.run_in_executor(
                executor, calculate_file_hash, temp_file_path
            )
        if not file_hash:
            raise Exception(f"Failed to calculate hash for {original_filename}")

        # Generate content-based filename
        content_based_filename = get_content_based_filename(
            original_filename, file_hash
        )
        final_file_path = os.path.join(config.UPLOAD_DIR, content_based_filename)

        # Check if file already exists and has been classified (deduplication)
        if os.path.exists(final_file_path):
            logger.info(
                f"File with same content already exists: {content_based_filename}"
            )
            # Remove temp file
            os.remove(temp_file_path)
            filename = content_based_filename
            file_path = final_file_path

            # Check if this file has already been classified
            existing_classification = self._get_existing_classification(filename, original_filename)
            if existing_classification:
                logger.info(
                    f"File {filename} already classified as {existing_classification.category} "
                    f"(confidence: {existing_classification.confidence:.3f}) - returning cached result"
                )
                return existing_classification, True
        else:
            # Move temp file to final location
            os.rename(temp_file_path, final_file_path)
            filename = content_based_filename
            file_path = final_file_path
            logger.info(
                f"Saved new file with content-based name: {content_based_filename}"
            )

        logger.debug(f"Final file path: {file_path}")

        # Process document - this will throw an exception if it fails
        # Run CPU-intensive processing in a thread pool to avoid blocking the event loop
        logger.debug(f"Starting document processing for {filename}...")
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor, processor.process_document, file_path, filename
            )
        logger.debug(f"Document processing completed for {filename}")

        # Extract classification information from the processor's category metadata
        # The most recent entry should be for this file
        category = "other"
        confidence = 0.0

        logger.debug(f"Looking for classification for filename: {filename}")
        logger.debug(
            f"Processor has category_metadata: {hasattr(processor, 'category_metadata')}"
        )

        if hasattr(processor, "category_metadata"):
            logger.debug(
                f"Available categories in metadata: {list(processor.category_metadata.keys())}"
            )
            # Find the most recent entry for this filename by timestamp
            most_recent_entry = None
            most_recent_timestamp = None

            for cat_name, documents in processor.category_metadata.items():
                if isinstance(documents, dict):
                    logger.debug(
                        f"Checking category '{cat_name}' with {len(documents)} documents"
                    )
                    if filename in documents:
                        doc = documents[filename]
                        timestamp = doc.get("timestamp", "")
                        logger.debug(
                            f"Found document in category '{cat_name}': category={doc.get('category', 'other')}, confidence={doc.get('confidence', 0.0)}, timestamp={timestamp}"
                        )

                        # Check if this is the most recent entry
                        if (
                            most_recent_timestamp is None
                            or timestamp > most_recent_timestamp
                        ):
                            most_recent_entry = doc
                            most_recent_timestamp = timestamp
                            logger.debug(
                                f"New most recent entry: category={doc.get('category', 'other')}, timestamp={timestamp}"
                            )

            if most_recent_entry:
                category = most_recent_entry.get("category", "other")
                confidence = most_recent_entry.get("confidence", 0.0)
                logger.debug(
                    f"Using most recent entry: category={category}, confidence={confidence}, timestamp={most_recent_timestamp}"
                )
            else:
                logger.debug("No document found in any category")

        logger.debug(
            f"Final classification result: category={category}, confidence={confidence}"
        )
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
