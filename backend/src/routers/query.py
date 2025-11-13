from fastapi import APIRouter, Depends
import logging
from src.models.schemas.query import QueryRequest, QueryResponse
from src.services.query_service import QueryService
from src.dependencies import get_query_service
from src.models.database import User
from src.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_index(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
    current_user: User = Depends(get_current_user),
) -> QueryResponse:
    """Handles user queries, searches the index, and returns relevant results."""
    logger.info(f"Received query: '{request.query}'")
    return query_service.search_documents(request.query)
