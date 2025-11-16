from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.models.database import ProcessingTaskStatus


class TaskEntry(BaseModel):
    """Individual task entry for API responses"""
    id: int
    document_id: str
    filename: str
    status: str  # ProcessingTaskStatus value
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TaskSummaryResponse(BaseModel):
    """Task summary with counts by status"""
    total_tasks: int
    pending: int
    processing: int
    completed: int
    failed: int


class TasksResponse(BaseModel):
    """List of tasks for current user with pagination"""
    tasks: List[TaskEntry]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkDeleteTasksRequest(BaseModel):
    """Request model for bulk task deletion"""
    task_ids: List[int]

