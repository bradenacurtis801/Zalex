"""Repository for ProcessingTask data access operations."""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from sqlmodel import Session, select

from src.models.database import (
    ProcessingTask as DBProcessingTask,
    ProcessingTaskStatus,
)

logger = logging.getLogger(__name__)


class ProcessingTaskRepository:
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

