"""Category router for document category management."""

import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile
from src.dependencies import get_category_service, get_current_user, require_admin, validate_uploaded_files
from src.models.schemas.category import CategoriesResponse, CategoryResponse, ClassifierInfoResponse
from src.models.database import User
from src.services.category_service import CategoryService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/categories", response_model=CategoriesResponse)
async def get_all_categories(
    skip: int = 0,
    limit: int = 100,
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> CategoriesResponse:
    """Get all available categories and their documents."""
    logger.info(f"Received request for all categories (skip={skip}, limit={limit})")
    return category_service.get_all_categories(skip=skip, limit=limit)


@router.get("/categories/summary")
async def get_categories_summary(
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a summary of document counts per category."""
    logger.info("Received request for categories summary")
    return category_service.get_categories_summary()


@router.get("/categories/training-metrics", response_model=ClassifierInfoResponse)
async def get_training_metrics(
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(require_admin()),
) -> ClassifierInfoResponse:
    """
    Get training metrics for all categories (admin only).
    
    Returns:
        ClassifierInfoResponse with classifier information and training metadata.
        Includes TrainingMetadata model with performance metrics, data distribution,
        model parameters, and feature extraction settings.
    """
    logger.info(f"Admin {current_user.id} requesting training metrics")
    return ClassifierInfoResponse(**category_service.get_training_metrics())


@router.get("/categories/{category}", response_model=CategoryResponse)
async def get_documents_by_category(
    category: str,
    skip: int = 0,
    limit: int = 100,
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """Get all documents in a specific category."""
    logger.info(f"Received request for category: {category} (skip={skip}, limit={limit})")

    return category_service.get_documents_by_category(category, skip=skip, limit=limit)


@router.post("/categories")
async def create_category(
    name: str = Form(...),
    description: str = Form(None),
    files: list[UploadFile] = File(...),
    category_service: CategoryService = Depends(get_category_service),
    validated_files: list[UploadFile] = Depends(validate_uploaded_files),
    current_user: User = Depends(require_admin()),
) -> dict:
    """
    Create a new category with training documents (admin only).
    
    Args:
        name: Category name
        description: Category description (optional)
        files: PDF files to use as training data for this category
        
    Returns:
        Dictionary with category info and uploaded document count
    """
    logger.info(f"Admin {current_user.id} creating category '{name}' with {len(files)} training document(s)")
    
    return await category_service.create_category_with_training_documents(
        name=name,
        description=description if description else None,
        files=validated_files,
        user_id=current_user.id,
    )

