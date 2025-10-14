import logging

from fastapi import APIRouter, Depends, File, UploadFile
from src.dependencies import get_upload_service
from src.models.upload import UploadResponse
from src.services.upload_service import UploadService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    files: list[UploadFile] = File(...),
    upload_service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    """Handles the file upload and initiates the processing pipeline."""
    logger.info(f"Received upload request with {len(files)} file(s)")
    return await upload_service.process_upload(files)
