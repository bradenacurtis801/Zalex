"""Exception handling and mapping for the application."""

from fastapi import HTTPException, status


class ScanProException(Exception):
    """Base exception for ScanPro application."""
    pass


class DocumentProcessingException(ScanProException):
    """Raised when document processing fails."""
    pass


class OCRNotAvailableException(DocumentProcessingException):
    """Raised when OCR engine (Tesseract) is not available."""
    pass


class FileProcessingException(ScanProException):
    """Raised when file processing fails."""
    pass


def map_to_http_exception(exc: Exception) -> HTTPException:
    """Map custom exceptions to HTTP exceptions."""
    mapping = {
        # ScanPro application exceptions
        OCRNotAvailableException: (status.HTTP_503_SERVICE_UNAVAILABLE, lambda exc: "OCR service is not available. Please ensure Tesseract is installed."),
        DocumentProcessingException: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: f"Document processing failed: {str(exc)}"),
        FileProcessingException: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: f"File processing failed: {str(exc)}"),
        ScanProException: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: f"Application error: {str(exc)}"),
        
        # File validation exceptions
        ValueError: (status.HTTP_400_BAD_REQUEST, lambda exc: str(exc)),
        FileNotFoundError: (status.HTTP_404_NOT_FOUND, lambda exc: f"File not found: {str(exc)}"),
        PermissionError: (status.HTTP_403_FORBIDDEN, lambda exc: f"Permission denied: {str(exc)}"),
        
        # Document processing exceptions
        RuntimeError: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: f"Processing error: {str(exc)}"),
        
        # Index/search exceptions
        IndexError: (status.HTTP_404_NOT_FOUND, lambda exc: f"Index error: {str(exc)}"),
        KeyError: (status.HTTP_404_NOT_FOUND, lambda exc: f"Key not found: {str(exc)}"),
        
        # Memory/resource exceptions
        MemoryError: (status.HTTP_507_INSUFFICIENT_STORAGE, lambda exc: f"Insufficient memory: {str(exc)}"),
        OSError: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: f"System error: {str(exc)}"),
    }
    
    if type(exc) in mapping:
        status_code, detail = mapping[type(exc)]
        if callable(detail):
            detail = detail(exc)
        return HTTPException(status_code=status_code, detail=detail)
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )
