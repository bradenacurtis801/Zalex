"""Category router for document category management."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_category_service
from src.models.category import CategoriesResponse, CategoryResponse
from src.services.category_service import CategoryService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/categories", response_model=CategoriesResponse)
async def get_all_categories(
    category_service: CategoryService = Depends(get_category_service),
) -> CategoriesResponse:
    """Get all available categories and their documents."""
    logger.info("Received request for all categories")
    return category_service.get_all_categories()


@router.get("/categories/{category}", response_model=CategoryResponse)
async def get_documents_by_category(
    category: str, category_service: CategoryService = Depends(get_category_service)
) -> CategoryResponse:
    """Get all documents in a specific category."""
    logger.info(f"Received request for category: {category}")

    # Validate category exists
    category_metadata = category_service.app_state.category_metadata
    if category not in category_metadata:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found. Available categories: {list(category_metadata.keys())}",
        )

    return category_service.get_documents_by_category(category)


@router.get("/categories/summary")
async def get_categories_summary(
    category_service: CategoryService = Depends(get_category_service),
) -> dict:
    """Get a summary of document counts per category."""
    logger.info("Received request for categories summary")
    return category_service.get_categories_summary()
