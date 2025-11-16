"""Repository for ProcessingTask data access operations."""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from sqlmodel import Session, select
from sqlalchemy import func

from src.models.database import (
    ProcessingTask as DBProcessingTask,
    ProcessingTaskStatus,
)

logger = logging.getLogger(__name__)


class TaskRepository:
    """Repository for ProcessingTask database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    @property
    def db(self) -> Session:
        """Get the database session."""
        return self._db

    def get_by_id(self, task_id: int) -> Optional[DBProcessingTask]:
        """
        Get a processing task by its ID.

        Args:
            task_id: Task ID

        Returns:
            ProcessingTask if found, None otherwise
        """
        return self._db.get(DBProcessingTask, task_id)

    def get_pending_by_document_id(self, document_id: str) -> Optional[DBProcessingTask]:
        """
        Get a pending task for a document.

        Args:
            document_id: Document ID

        Returns:
            Pending ProcessingTask if found, None otherwise
        """
        stmt = (
            select(DBProcessingTask)
            .where(DBProcessingTask.document_id == document_id)
            .where(DBProcessingTask.status == ProcessingTaskStatus.PENDING)
        )
        return self._db.exec(stmt).first()

    def get_all_pending(self) -> List[DBProcessingTask]:
        """
        Get all pending tasks.

        Returns:
            List of pending ProcessingTask objects
        """
        stmt = select(DBProcessingTask).where(
            DBProcessingTask.status == ProcessingTaskStatus.PENDING
        )
        return list(self._db.exec(stmt).all())

    def get_all_processing(self) -> List[DBProcessingTask]:
        """
        Get all tasks in PROCESSING status.

        Returns:
            List of ProcessingTask objects in PROCESSING status
        """
        stmt = select(DBProcessingTask).where(
            DBProcessingTask.status == ProcessingTaskStatus.PROCESSING
        )
        return list(self._db.exec(stmt).all())

    def create(
        self,
        document_id: str,
        filename: str,
        user_id: Optional[int] = None,
        status: ProcessingTaskStatus = ProcessingTaskStatus.PENDING,
    ) -> DBProcessingTask:
        """
        Create a new processing task.

        Args:
            document_id: Document ID
            filename: Document filename
            user_id: User ID (optional)
            status: Task status (default: PENDING)

        Returns:
            Created ProcessingTask record
        """
        task = DBProcessingTask(
            document_id=document_id,
            filename=filename,
            user_id=user_id,
            status=status,
        )
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    def update_status(
        self,
        task: DBProcessingTask,
        status: ProcessingTaskStatus,
        error: Optional[str] = None,
    ) -> DBProcessingTask:
        """
        Update task status.

        Args:
            task: The processing task to update
            status: New status
            error: Error message if failed (optional)

        Returns:
            Updated ProcessingTask
        """
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        if error is not None:
            task.error = error
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    def reset_processing_to_pending(self, tasks: List[DBProcessingTask]) -> None:
        """
        Reset tasks from PROCESSING to PENDING status.

        Args:
            tasks: List of tasks to reset
        """
        for task in tasks:
            task.status = ProcessingTaskStatus.PENDING
            task.error = None
            task.updated_at = datetime.now(timezone.utc)
            self._db.add(task)
        self._db.commit()

    def delete(self, task: DBProcessingTask) -> None:
        """
        Delete a processing task.

        Args:
            task: The processing task to delete
        """
        self._db.delete(task)
        self._db.commit()
        logger.debug(f"Deleted processing task {task.id} for document {task.document_id}")

    def delete_by_id(self, task_id: int) -> bool:
        """
        Delete a processing task by ID.

        Args:
            task_id: Task ID to delete

        Returns:
            True if task was deleted, False if not found
        """
        task = self.get_by_id(task_id)
        if task:
            self.delete(task)
            return True
        return False

    def delete_by_ids(self, task_ids: List[int]) -> int:
        """
        Delete multiple processing tasks by their IDs.

        Args:
            task_ids: List of task IDs to delete

        Returns:
            Number of tasks successfully deleted
        """
        if not task_ids:
            return 0
        
        # Get all tasks by IDs
        stmt = select(DBProcessingTask).where(
            DBProcessingTask.id.in_(task_ids)
        )
        tasks_to_delete = list(self._db.exec(stmt).all())
        
        # Delete all tasks
        for task in tasks_to_delete:
            self._db.delete(task)
        
        self._db.commit()
        deleted_count = len(tasks_to_delete)
        logger.debug(f"Deleted {deleted_count} processing task(s)")
        return deleted_count

    def get_all_by_user_id(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> tuple[List[DBProcessingTask], int]:
        """
        Get paginated tasks for a specific user.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of ProcessingTask objects, total count)
        """
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count efficiently using COUNT
        count_stmt = select(func.count(DBProcessingTask.id)).where(
            DBProcessingTask.user_id == user_id
        )
        total_count = self._db.exec(count_stmt).one()
        
        # Get paginated results
        stmt = (
            select(DBProcessingTask)
            .where(DBProcessingTask.user_id == user_id)
            .order_by(DBProcessingTask.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        tasks = list(self._db.exec(stmt).all())
        
        return tasks, total_count

    def get_task_counts_by_user_id(self, user_id: int) -> dict[str, int]:
        """
        Get task counts by status for a specific user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with status counts: {
                'total': int,
                'pending': int,
                'processing': int,
                'completed': int,
                'failed': int
            }
        """
        # Use efficient SQL COUNT queries instead of loading all tasks
        # Get total count
        total_stmt = select(func.count(DBProcessingTask.id)).where(
            DBProcessingTask.user_id == user_id
        )
        total = self._db.exec(total_stmt).one()
        
        # Count by status
        pending_stmt = select(func.count(DBProcessingTask.id)).where(
            DBProcessingTask.user_id == user_id,
            DBProcessingTask.status == ProcessingTaskStatus.PENDING
        )
        pending = self._db.exec(pending_stmt).one()
        
        processing_stmt = select(func.count(DBProcessingTask.id)).where(
            DBProcessingTask.user_id == user_id,
            DBProcessingTask.status == ProcessingTaskStatus.PROCESSING
        )
        processing = self._db.exec(processing_stmt).one()
        
        completed_stmt = select(func.count(DBProcessingTask.id)).where(
            DBProcessingTask.user_id == user_id,
            DBProcessingTask.status == ProcessingTaskStatus.COMPLETED
        )
        completed = self._db.exec(completed_stmt).one()
        
        failed_stmt = select(func.count(DBProcessingTask.id)).where(
            DBProcessingTask.user_id == user_id,
            DBProcessingTask.status == ProcessingTaskStatus.FAILED
        )
        failed = self._db.exec(failed_stmt).one()
        
        return {
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed
        }

