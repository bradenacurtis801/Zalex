"""Task service for managing processing tasks."""

import logging
from typing import List

from src.core.exceptions import TaskNotFoundException
from src.models.schemas.task import TaskEntry, TasksResponse, TaskSummaryResponse
from src.repositories import DataRepository
from src.routers.task import delete_task

logger = logging.getLogger(__name__)


class TaskService:
    """Service for handling processing task operations."""

    def __init__(
        self,
        data_repo: DataRepository,
    ):
        self._data_repo = data_repo

    def get_task_summary(self, user_id: int) -> TaskSummaryResponse:
        """
        Get task summary (counts by status) for a user.

        Args:
            user_id: User ID

        Returns:
            TaskSummaryResponse with counts by status
        """
        logger.info(f"Retrieving task summary for user {user_id}")
        
        counts = self._data_repo.get_task_counts_by_user_id(user_id)
        
        return TaskSummaryResponse(
            total_tasks=counts['total'],
            pending=counts['pending'],
            processing=counts['processing'],
            completed=counts['completed'],
            failed=counts['failed']
        )

    def get_user_tasks(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> TasksResponse:
        """
        Get paginated tasks for a user.

        Args:
            user_id: User ID
            page: Page number (1-indexed, default: 1)
            page_size: Number of items per page (default: 20)

        Returns:
            TasksResponse with paginated list of tasks
        """
        logger.info(f"Retrieving tasks for user {user_id} (page {page}, size {page_size})")
        
        # FastAPI Query validation ensures: page >= 1, page_size >= 1, page_size <= 100
        tasks, total_count = self._data_repo.get_all_tasks_by_user_id(
            user_id, 
            page=page, 
            page_size=page_size
        )
        
        # Convert to TaskEntry models
        task_entries: List[TaskEntry] = [
            TaskEntry(
                id=task.id,
                document_id=task.document_id,
                filename=task.filename,
                status=task.status.value,
                error=task.error,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            for task in tasks
        ]
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        return TasksResponse(
            tasks=task_entries,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def delete_task(self, task_id: int, user_id: int) -> None:
        """
        Delete a task if it belongs to the user.

        Args:
            task_id: Task ID to delete
            user_id: User ID (to verify ownership)

        Raises:
            TaskNotFoundException: If task not found or doesn't belong to user
        """
        logger.info(f"Attempting to delete task {task_id} for user {user_id}")
        
        task = self._data_repo.get_task(task_id)
        
        if not task:
            logger.warning(f"Task {task_id} not found")
            raise TaskNotFoundException(f"Task {task_id} not found")
        
        # Verify task belongs to user
        if task.user_id != user_id:
            logger.warning(f"Task {task_id} does not belong to user {user_id}")
            raise TaskNotFoundException(f"Task {task_id} does not belong to user")
        
        # Delete the task
        self._processing_task_repo.delete(task)
        logger.info(f"Successfully deleted task {task_id} for user {user_id}")

    def delete_tasks(self, task_ids: List[int], user_id: int) -> dict:
        """
        Delete multiple tasks if they belong to the user.

        Args:
            task_ids: List of task IDs to delete
            user_id: User ID (to verify ownership)

        Returns:
            Dictionary with deletion results: {
                'message': str,  # Human-readable message
                'deleted': int,  # Number of tasks successfully deleted
                'not_found': List[int],  # Task IDs not found
                'unauthorized': List[int]  # Task IDs that don't belong to user
            }

        Raises:
            TaskNotFoundException: If no tasks were found or authorized
        """
        if not task_ids:
            return {
                'message': 'No tasks to delete',
                'deleted': 0,
                'not_found': [],
                'unauthorized': []
            }

        logger.info(f"Attempting to delete {len(task_ids)} task(s) for user {user_id}")

        # Get all tasks by IDs
        tasks = []
        not_found = []
        for task_id in task_ids:
            task = self._data_repo.get_task(task_id)
            if task:
                tasks.append(task)
            else:
                not_found.append(task_id)
                logger.warning(f"Task {task_id} not found")

        # Verify ownership and separate authorized/unauthorized
        authorized_tasks = []
        unauthorized = []
        for task in tasks:
            if task.user_id == user_id:
                authorized_tasks.append(task)
            else:
                unauthorized.append(task.id)
                logger.warning(f"Task {task.id} does not belong to user {user_id}")

        # Delete authorized tasks
        if authorized_tasks:
            task_ids_to_delete = [task.id for task in authorized_tasks]
            deleted_count = self._data_repo.delete_task(task_ids_to_delete)
            logger.info(f"Successfully deleted {deleted_count} task(s) for user {user_id}")
        else:
            deleted_count = 0

        # If no tasks were deleted and there were tasks to delete, raise exception
        if deleted_count == 0 and (not_found or unauthorized):
            if unauthorized:
                raise TaskNotFoundException(f"Tasks {unauthorized} do not belong to user")
            if not_found:
                raise TaskNotFoundException(f"Tasks {not_found} not found")

        # Build response message
        message = f"Successfully deleted {deleted_count} task(s)"
        if not_found:
            message += f". {len(not_found)} task(s) not found"
        if unauthorized:
            message += f". {len(unauthorized)} task(s) unauthorized"

        return {
            'message': message,
            'deleted': deleted_count,
            'not_found': not_found,
            'unauthorized': unauthorized
        }

