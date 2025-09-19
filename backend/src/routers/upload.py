from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
import config as config
from app_state import get_app_state
from src.models.upload import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()
app_state = get_app_state()

@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)):
    """Handles the file upload and initiates the processing pipeline."""
    logger.info(f"Received upload request with {len(files)} file(s)")
    logger.debug(f"File names: {[f.filename for f in files]}")
    
    if not files or files[0].filename == '':
        logger.debug("No files provided or empty filename")
        raise HTTPException(status_code=400, detail="No selected files")

    success_count = 0
    error_count = 0

    # Get the document processor
    processor = app_state.document_processor
    logger.debug(f"Document processor status: {'Available' if processor else 'None'}")
    logger.debug(f"Upload directory: {config.UPLOAD_DIR}")

    for i, file in enumerate(files):
        logger.debug(f"Processing file {i+1}/{len(files)}: {file.filename}")
        try:
            filename = file.filename
            file_path = os.path.join(config.UPLOAD_DIR, filename)
            logger.debug(f"File path: {file_path}")
            
            # Ensure upload directory exists
            os.makedirs(config.UPLOAD_DIR, exist_ok=True)
            logger.debug(f"Upload directory ensured: {config.UPLOAD_DIR}")
            
            # Save file
            logger.debug(f"Reading file content for {filename}...")
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            logger.debug(f"File saved successfully. Size: {len(content)} bytes")

            # Process document
            logger.debug(f"Starting document processing for {filename}...")
            result = processor.process_document(file_path, filename)
            logger.debug(f"Processing result: {result}")
            
            if result['status'] == 'success':
                success_count += 1
                logger.debug(f"Successfully processed {filename}")
            else:
                error_count += 1
                logger.debug(f"Failed to process {filename}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error saving or processing file {file.filename}: {e}")
            logger.debug(f"Exception details for {file.filename}: {type(e).__name__}: {str(e)}")
            error_count += 1

    message = f"Enrollment process finished. Successfully indexed {success_count} file(s)."
    if error_count > 0:
        message += f" Failed to process {error_count} file(s)."

    logger.info(f"Upload processing complete. Success: {success_count}, Errors: {error_count}")
    logger.debug(f"Final message: {message}")
    return UploadResponse(message=message)
