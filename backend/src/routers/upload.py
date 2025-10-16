import logging
import os

import config
from fastapi import APIRouter, Depends, File, HTTPException
from fastapi import Path as FastAPIPath
from fastapi import UploadFile
from fastapi.responses import FileResponse, JSONResponse
from src.dependencies import get_pdf_service, get_upload_service
from src.models.upload import UploadResponse
from src.services.pdf_service import PDFService
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


@router.get("/documents/{filename}/content")
async def get_document_content(
    filename: str = FastAPIPath(
        ...,
        regex=r"^[a-zA-Z0-9._-]+$",
        min_length=1,
        max_length=255,
        description="Document filename (content-based hash format)",
    )
):
    """
    Get the content of a document for viewing.

    Args:
        filename: Name of the file to retrieve

    Returns:
        File content or text content
    """
    logger.info(f"Received request for document content: {filename}")

    # Security check - ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(config.UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")

    # Determine file type
    file_extension = filename.lower().split(".")[-1]

    if file_extension in ["pdf"]:
        # For PDFs, return with proper MIME type for browser display
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": "inline"},
        )
    elif file_extension in ["jpg", "jpeg", "png", "gif", "bmp"]:
        # For images, return with proper MIME type
        media_type = (
            f"image/{file_extension}" if file_extension != "jpg" else "image/jpeg"
        )
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": "inline"},
        )
    else:
        # For text files, return the content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content, "filename": filename}
        except UnicodeDecodeError:
            # If it's not a text file, return as binary
            return FileResponse(
                path=file_path, media_type="application/octet-stream", filename=filename
            )


@router.get("/documents/{filename}/download")
async def download_document(
    filename: str = FastAPIPath(
        ...,
        regex=r"^[a-zA-Z0-9._-]+$",
        min_length=1,
        max_length=255,
        description="Document filename (content-based hash format)",
    )
):
    """
    Download a document file.

    Args:
        filename: Name of the file to download

    Returns:
        File download response
    """
    logger.info(f"Received download request for: {filename}")

    # Security check - ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(config.UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment"},
    )


@router.get("/documents/{filename}/pages")
async def get_pdf_pages(
    filename: str = FastAPIPath(
        ...,
        regex=r"^[a-zA-Z0-9._-]+$",
        min_length=1,
        max_length=255,
        description="PDF filename (content-based hash format)",
    ),
    pdf_service: PDFService = Depends(get_pdf_service),
):
    """
    Convert PDF to images and return page information.

    Args:
        filename: Name of the PDF file
        pdf_service: PDF service instance

    Returns:
        JSON with page information and image URLs
    """
    logger.info(f"Received request for PDF pages: {filename}")

    try:
        result = pdf_service.convert_pdf_to_pages(filename, max_pages=20)

        # Return with caching headers for browser caching
        response = JSONResponse(content=result)
        response.headers["Cache-Control"] = "public, max-age=3600"  # Cache for 1 hour
        response.headers["ETag"] = (
            f'"{filename}"'  # Use filename as ETag for cache validation
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error converting PDF to pages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to convert PDF: {str(e)}")


@router.get("/pdf-cache/stats")
async def get_pdf_cache_stats(pdf_service: PDFService = Depends(get_pdf_service)):
    """
    Get PDF cache statistics.

    Args:
        pdf_service: PDF service instance

    Returns:
        Cache statistics
    """
    logger.info("Received request for PDF cache stats")

    try:
        stats = pdf_service.get_cache_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache stats: {str(e)}"
        )


@router.post("/pdf-cache/cleanup")
async def cleanup_pdf_cache(pdf_service: PDFService = Depends(get_pdf_service)):
    """
    Clean up expired PDF cache files.

    Args:
        pdf_service: PDF service instance

    Returns:
        Cleanup results
    """
    logger.info("Received request to cleanup PDF cache")

    try:
        cleaned_count = pdf_service.cleanup_expired_cache()
        return {
            "success": True,
            "cleaned_files": cleaned_count,
            "message": f"Cleaned up {cleaned_count} expired cache files",
        }

    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup cache: {str(e)}"
        )
