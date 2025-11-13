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

