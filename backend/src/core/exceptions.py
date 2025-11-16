"""Exception handling and mapping for the application."""

from fastapi import HTTPException, status


class ScanProException(Exception):
    """Base exception for ScanPro application."""
    def __init__(self, message: str = "An error occurred in the ScanPro application"):
        super().__init__(message)


class DocumentProcessingException(ScanProException):
    """Raised when document processing fails."""
    def __init__(self, message: str = "Document processing failed. Please try again."):
        super().__init__(message)


class OCRNotAvailableException(DocumentProcessingException):
    """Raised when OCR engine (Tesseract) is not available."""
    def __init__(self, message: str = "OCR service is not available. Please ensure Tesseract is installed."):
        super().__init__(message)


class ClassifierNotAvailableException(DocumentProcessingException):
    """Raised when document classifier is not available for processing."""
    def __init__(self, message: str = "Document classification service is not available. Please contact support."):
        super().__init__(message)


class FileProcessingException(ScanProException):
    """Raised when file processing fails."""
    def __init__(self, message: str = "File processing failed. Please try again."):
        super().__init__(message)


class UnsupportedFileTypeError(FileProcessingException):
    """Raised when an unsupported file type is uploaded."""
    def __init__(self, message: str = "Unsupported file type. Only PDF and image files are allowed."):
        super().__init__(message)


class FeedbackException(ScanProException):
    """Raised when feedback operations fail."""
    def __init__(self, message: str = "Feedback operation failed. Please try again."):
        super().__init__(message)


class DocumentNotFoundError(FeedbackException):
    """Raised when a document is not found for reclassification."""
    def __init__(self, message: str = "Document not found."):
        super().__init__(message)


class CategoryNotFoundError(FeedbackException):
    """Raised when a category is not found."""
    def __init__(self, message: str = "Category not found."):
        super().__init__(message)


class CategoryAlreadyExistsError(ScanProException):
    """Raised when trying to create a category that already exists."""
    def __init__(self, message: str = "Category already exists."):
        super().__init__(message)


class TaskNotFoundException(ScanProException):
    """Raised when a processing task is not found."""
    def __init__(self, message: str = "Task not found or does not belong to user."):
        super().__init__(message)


class InvalidModelDirectoryError(ScanProException):
    """Raised when a model directory is invalid or missing required files."""
    def __init__(self, message: str = "Invalid model directory. Required files are missing."):
        super().__init__(message)


class InvalidModelMetadataError(ScanProException):
    """Raised when model metadata is invalid or missing required fields."""
    def __init__(self, message: str = "Invalid model metadata. Required fields are missing."):
        super().__init__(message)

# Authentication exceptions
class AuthenticationException(Exception):
    """Base class for authentication exceptions"""
    def __init__(self, message: str = "Authentication error"):
        super().__init__(message)

class UserNotFoundException(AuthenticationException):
    """Raised when user is not found"""
    def __init__(self, message: str = "User not found"):
        super().__init__(message)

class InvalidCredentialsException(AuthenticationException):
    """Raised when credentials are invalid"""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)

class PermissionDeniedException(AuthenticationException):
    """Raised when user lacks required permissions"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message)

class SessionExpiredException(AuthenticationException):
    """Raised when token has expired"""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)

class UserAlreadyExistsException(AuthenticationException):
    """Raised when trying to create a user that already exists"""
    def __init__(self, message: str = "User already exists"):
        super().__init__(message)


def map_to_http_exception(exc: Exception) -> HTTPException:
    """Map custom exceptions to HTTP exceptions."""
    mapping = {
        # ScanPro application exceptions
        OCRNotAvailableException: (status.HTTP_503_SERVICE_UNAVAILABLE, lambda exc: str(exc)),
        ClassifierNotAvailableException: (status.HTTP_503_SERVICE_UNAVAILABLE, lambda exc: str(exc)),
        DocumentProcessingException: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: str(exc)),
        FileProcessingException: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: str(exc)),
        UnsupportedFileTypeError: (status.HTTP_400_BAD_REQUEST, lambda exc: str(exc)),
        DocumentNotFoundError: (status.HTTP_404_NOT_FOUND, lambda exc: str(exc)),
        CategoryNotFoundError: (status.HTTP_404_NOT_FOUND, lambda exc: str(exc)),
        CategoryAlreadyExistsError: (status.HTTP_400_BAD_REQUEST, lambda exc: str(exc)),
        TaskNotFoundException: (status.HTTP_404_NOT_FOUND, lambda exc: str(exc)),
        FeedbackException: (status.HTTP_400_BAD_REQUEST, lambda exc: str(exc)),
        ScanProException: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: str(exc)),
        
        # File validation exceptions
        ValueError: (status.HTTP_400_BAD_REQUEST, lambda exc: str(exc)),
        FileNotFoundError: (status.HTTP_404_NOT_FOUND, lambda exc: str(exc)),
        PermissionError: (status.HTTP_403_FORBIDDEN, lambda exc: str(exc)),
        # Document processing exceptions
        RuntimeError: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: str(exc)),
        # Index/search exceptions
        IndexError: (status.HTTP_404_NOT_FOUND, lambda exc: str(exc)),
        KeyError: (status.HTTP_404_NOT_FOUND, lambda exc: str(exc)),
        # Memory/resource exceptions
        MemoryError: (status.HTTP_507_INSUFFICIENT_STORAGE, lambda exc: str(exc)),
        OSError: (status.HTTP_500_INTERNAL_SERVER_ERROR, lambda exc: str(exc)),

        # Authentication exceptions
        UserNotFoundException: (status.HTTP_404_NOT_FOUND, lambda exc: str(exc)),
        InvalidCredentialsException: (status.HTTP_401_UNAUTHORIZED, lambda exc: str(exc)),
        PermissionDeniedException: (status.HTTP_403_FORBIDDEN, lambda exc: str(exc)),
        SessionExpiredException: (status.HTTP_401_UNAUTHORIZED, lambda exc: str(exc)),
        UserAlreadyExistsException: (status.HTTP_400_BAD_REQUEST, lambda exc: str(exc)),
        AuthenticationException: (status.HTTP_401_UNAUTHORIZED, lambda exc: str(exc)),
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
