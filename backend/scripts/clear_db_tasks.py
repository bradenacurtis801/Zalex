#!/usr/bin/env python3
"""
Script to clear all ProcessingTask records from the database.
This will delete all pending, processing, completed, and failed tasks.
"""

import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from src.models.database import ProcessingTask
import config
from src.core.constants import get_database_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clear_processing_tasks():
    """Clear all ProcessingTask records from the database."""
    
    logger.info("Starting processing task cleanup...")
    
    # Create database engine
    engine = create_engine(
        config.settings.database_url,
        echo=config.LOG_LEVEL == "DEBUG",
        **get_database_config()
    )
    
    with Session(engine) as session:
        try:
            # Get counts before deletion for reporting
            all_tasks = session.exec(select(ProcessingTask)).all()
            task_count = len(all_tasks)
            
            # Count by status
            from src.models.database import ProcessingTaskStatus
            pending_count = len(session.exec(select(ProcessingTask).where(ProcessingTask.status == ProcessingTaskStatus.PENDING)).all())
            processing_count = len(session.exec(select(ProcessingTask).where(ProcessingTask.status == ProcessingTaskStatus.PROCESSING)).all())
            completed_count = len(session.exec(select(ProcessingTask).where(ProcessingTask.status == ProcessingTaskStatus.COMPLETED)).all())
            failed_count = len(session.exec(select(ProcessingTask).where(ProcessingTask.status == ProcessingTaskStatus.FAILED)).all())
            
            logger.info(f"Current task counts:")
            logger.info(f"  Total tasks: {task_count}")
            logger.info(f"    - PENDING: {pending_count}")
            logger.info(f"    - PROCESSING: {processing_count}")
            logger.info(f"    - COMPLETED: {completed_count}")
            logger.info(f"    - FAILED: {failed_count}")
            
            if task_count == 0:
                logger.info("No processing tasks found to clear.")
                return
            
            # Confirm deletion
            print(f"\n⚠️  WARNING: This will delete {task_count} processing task(s)!")
            response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
            
            if response != 'yes':
                logger.info("Operation cancelled by user.")
                return
            
            logger.info("Starting deletion process...")
            
            # Delete all processing tasks
            for task in all_tasks:
                session.delete(task)
            
            # Commit deletion
            session.commit()
            
            # Verify deletion
            remaining_tasks = len(session.exec(select(ProcessingTask)).all())
            
            logger.info("✅ Processing task cleanup completed successfully!")
            logger.info(f"Remaining tasks: {remaining_tasks}")
            
            if remaining_tasks == 0:
                logger.info("🎉 All processing tasks have been cleared!")
            else:
                logger.warning(f"⚠️  {remaining_tasks} tasks still remain (this shouldn't happen)")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            session.rollback()
            raise


def main():
    """Main function."""
    print("🗑️  ScanPro Processing Task Cleanup Script")
    print("=" * 50)
    print(f"Database: {config.settings.database_url}")
    print(f"Environment: {config.settings.node_env_value}")
    print("=" * 50)
    
    try:
        clear_processing_tasks()
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

