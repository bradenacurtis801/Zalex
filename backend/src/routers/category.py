"""Category router for document category management."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_category_service, get_current_user
from src.models.schemas.category import CategoriesResponse, CategoryResponse
from src.models.database import User
from src.services.category_service import CategoryService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/categories", response_model=CategoriesResponse)
async def get_all_categories(
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> CategoriesResponse:
    """Get all available categories and their documents."""
    logger.info("Received request for all categories")
    return category_service.get_all_categories()


@router.get("/categories/summary")
async def get_categories_summary(
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a summary of document counts per category."""
    logger.info("Received request for categories summary")
    return category_service.get_categories_summary()


@router.get("/categories/{category}", response_model=CategoryResponse)
async def get_documents_by_category(
    category: str, 
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """Get all documents in a specific category."""
    logger.info(f"Received request for category: {category}")

    # Validate category exists by getting available categories
    available_categories = category_service._get_model_categories()
    if category not in available_categories:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found. Available categories: {available_categories}",
        )

    return category_service.get_documents_by_category(category)
