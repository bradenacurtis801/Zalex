"""Task router for processing task endpoints."""

import logging
from fastapi import APIRouter, Depends, Query

from src.models.database import User
from src.models.schemas.task import TaskSummaryResponse, TasksResponse, BulkDeleteTasksRequest
from src.services.task_service import TaskService
from src.dependencies import get_current_user, get_task_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/summary", response_model=TaskSummaryResponse)
async def get_task_summary(
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskSummaryResponse:
    """
    Get task summary (counts by status) for the current user.
    
    Returns:
        TaskSummaryResponse with counts of tasks by status
    """
    logger.info(f"Getting task summary for user {current_user.id}")
    return task_service.get_task_summary(current_user.id)


@router.get("", response_model=TasksResponse)
async def get_user_tasks(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TasksResponse:
    """
    Get paginated processing tasks for the current user.
    
    Args:
        page: Page number (default: 1)
        page_size: Number of items per page (default: 20, max: 100)
    
    Returns:
        TasksResponse with paginated list of tasks
    """
    logger.info(f"Getting tasks for user {current_user.id} (page {page}, size {page_size})")
    return task_service.get_user_tasks(current_user.id, page=page, page_size=page_size)


@router.delete("", response_model=dict)
async def delete_tasks(
    request: BulkDeleteTasksRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """
    Delete multiple processing tasks for the current user in a single request.
    
    Args:
        request: BulkDeleteTasksRequest containing list of task IDs
        
    Returns:
        Success message with deletion results
    """
    logger.info(f"Deleting {len(request.task_ids)} task(s) for user {current_user.id}")
    
    return task_service.delete_tasks(request.task_ids, current_user.id)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """
    Delete a processing task for the current user.
    
    Args:
        task_id: Task ID to delete
        
    Returns:
        Success message
    """
    logger.info(f"Deleting task {task_id} for user {current_user.id}")
    
    task_service.delete_task(task_id, current_user.id)
    
    return {"message": f"Task {task_id} deleted successfully"}

