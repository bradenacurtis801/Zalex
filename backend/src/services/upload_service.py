"""Upload service for handling file uploads and processing."""

import os
import logging
from typing import List, Dict, Any
from fastapi import UploadFile
import config as config
from app_state import get_app_state
from src.models.upload import UploadResponse

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
        
        if not files or files[0].filename == '':
            logger.debug("No files provided or empty filename")
            raise ValueError("No selected files")
        
        # Get the document processor
        processor = self.app_state.document_processor
        logger.debug(f"Document processor status: {'Available' if processor else 'None'}")
        logger.debug(f"Upload directory: {config.UPLOAD_DIR}")
        
        # Ensure upload directory exists
        self._ensure_upload_directory()
        
        # Process all files - if any fail, the whole operation fails
        for i, file in enumerate(files):
            logger.debug(f"Processing file {i+1}/{len(files)}: {file.filename}")
            await self._process_single_file(file, processor)
            logger.debug(f"Successfully processed {file.filename}")
        
        message = f"Successfully processed {len(files)} file(s)."
        logger.info(f"Upload processing complete. All {len(files)} files processed successfully.")
        logger.debug(f"Final message: {message}")
        
        return UploadResponse(message=message)
    
    def _ensure_upload_directory(self) -> None:
        """Ensure the upload directory exists."""
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        logger.debug(f"Upload directory ensured: {config.UPLOAD_DIR}")
    
    async def _process_single_file(self, file: UploadFile, processor) -> None:
        """
        Process a single uploaded file.
        
        Args:
            file: The uploaded file
            processor: Document processor instance
            
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
        processor.process_document(file_path, filename)
        logger.debug(f"Document processing completed for {filename}")
    
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
    
