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


class FeedbackException(ScanProException):
    """Raised when feedback operations fail."""

    pass


class DocumentNotFoundError(FeedbackException):
    """Raised when a document is not found for reclassification."""

    pass


class CategoryNotFoundError(FeedbackException):
    """Raised when a category is not found."""

    pass


def map_to_http_exception(exc: Exception) -> HTTPException:
    """Map custom exceptions to HTTP exceptions."""
    mapping = {
        # ScanPro application exceptions
        OCRNotAvailableException: (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            lambda exc: "OCR service is not available. Please ensure Tesseract is installed.",
        ),
        DocumentProcessingException: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            lambda exc: "Document processing failed. Please try again.",  # Generic for security
        ),
        FileProcessingException: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            lambda exc: "File processing failed. Please try again.",  # Generic for security
        ),
        DocumentNotFoundError: (
            status.HTTP_404_NOT_FOUND,
            lambda exc: str(exc),  # Safe to expose - user-friendly message
        ),
        CategoryNotFoundError: (
            status.HTTP_404_NOT_FOUND,
            lambda exc: str(exc),  # Safe to expose - user-friendly message
        ),
        FeedbackException: (
            status.HTTP_400_BAD_REQUEST,
            lambda exc: "Feedback operation failed. Please try again.",  # Generic message for security
        ),
        ScanProException: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            lambda exc: "An unexpected error occurred. Please try again.",  # Generic for security
        ),
        # File validation exceptions
        ValueError: (status.HTTP_400_BAD_REQUEST, lambda exc: str(exc)),
        FileNotFoundError: (
            status.HTTP_404_NOT_FOUND,
            lambda exc: "File not found.",  # Generic for security
        ),
        PermissionError: (
            status.HTTP_403_FORBIDDEN,
            lambda exc: "Permission denied.",  # Generic for security
        ),
        # Document processing exceptions
        RuntimeError: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            lambda exc: "Processing error. Please try again.",  # Generic for security
        ),
        # Index/search exceptions
        IndexError: (
            status.HTTP_404_NOT_FOUND,
            lambda exc: "Resource not found.",
        ),  # Generic for security
        KeyError: (
            status.HTTP_404_NOT_FOUND,
            lambda exc: "Resource not found.",
        ),  # Generic for security
        # Memory/resource exceptions
        MemoryError: (
            status.HTTP_507_INSUFFICIENT_STORAGE,
            lambda exc: "Insufficient resources. Please try again.",  # Generic for security
        ),
        OSError: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            lambda exc: "System error. Please try again.",  # Generic for security
        ),
    }

    if type(exc) in mapping:
        status_code, detail = mapping[type(exc)]
        if callable(detail):
            detail = detail(exc)
        return HTTPException(status_code=status_code, detail=detail)

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )
