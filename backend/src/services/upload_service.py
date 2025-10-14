"""Upload service for handling file uploads and processing."""

import logging
import os
from typing import Any, Dict, List

import config as config
from app_state import get_app_state
from fastapi import UploadFile
from src.models.upload import DocumentClassification, UploadResponse

logger = logging.getLogger(__name__)


class UploadService:
    """Service for handling file uploads and document processing."""

    def __init__(self):
        self.app_state = get_app_state()

    async def process_upload(self, files: List[UploadFile]) -> UploadResponse:
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

        # Get the document processor
        processor = self.app_state.document_processor
        logger.debug(
            f"Document processor status: {'Available' if processor else 'None'}"
        )
        logger.debug(f"Upload directory: {config.UPLOAD_DIR}")

        # Ensure upload directory exists
        self._ensure_upload_directory()

        # Process all files - if any fail, the whole operation fails
        classifications = []
        for i, file in enumerate(files):
            logger.debug(f"Processing file {i+1}/{len(files)}: {file.filename}")
            classification = await self._process_single_file(file, processor)
            if classification:
                classifications.append(classification)
            logger.debug(f"Successfully processed {file.filename}")

        message = f"Successfully processed {len(files)} file(s)."
        logger.info(
            f"Upload processing complete. All {len(files)} files processed successfully."
        )
        logger.debug(f"Final message: {message}")

        return UploadResponse(message=message, classifications=classifications)

    def _ensure_upload_directory(self) -> None:
        """Ensure the upload directory exists."""
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        logger.debug(f"Upload directory ensured: {config.UPLOAD_DIR}")

    async def _process_single_file(
        self, file: UploadFile, processor
    ) -> DocumentClassification:
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
        filename = file.filename
        file_path = os.path.join(config.UPLOAD_DIR, filename)
        logger.debug(f"File path: {file_path}")

        # Save file
        await self._save_file(file, file_path)

        # Process document - this will throw an exception if it fails
        logger.debug(f"Starting document processing for {filename}...")
        result = processor.process_document(file_path, filename)
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
                logger.debug(
                    f"Checking category '{cat_name}' with {len(documents)} documents"
                )
                for doc in documents:
                    if doc.get("filename") == filename:
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
        return DocumentClassification(
            filename=filename, category=category, confidence=confidence
        )

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
