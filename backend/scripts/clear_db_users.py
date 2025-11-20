#!/usr/bin/env python3
"""
Script to clear all users from the database.
This will delete all users and their associated sessions.
WARNING: This will make the application unusable until new users are created.
"""

import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from src.models.database import (
    User,
    Session as UserSession,
    Document,
    DocumentClassification,
    DocumentFeedback,
    ProcessingTask
)
import config
from src.core.constants import get_database_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clear_users():
    """Clear all users and their sessions from the database."""
    
    logger.info("Starting user cleanup...")
    
    # Create database engine
    engine = create_engine(
        config.settings.database_url,
        echo=config.LOG_LEVEL == "DEBUG",
        **get_database_config()
    )
    
    with Session(engine) as session:
        try:
            # Get counts before deletion for reporting
            user_count = len(session.exec(select(User)).all())
            session_count = len(session.exec(select(UserSession)).all())
            # Count documents/tasks with user associations (for info only)
            documents_with_user = len(session.exec(select(Document).where(Document.user_id.isnot(None))).all())
            tasks_with_user = len(session.exec(select(ProcessingTask).where(ProcessingTask.user_id.isnot(None))).all())
            
            logger.info(f"Current data counts:")
            logger.info(f"  Users: {user_count}")
            logger.info(f"  Sessions: {session_count}")
            logger.info(f"  Documents with user association: {documents_with_user}")
            logger.info(f"  Processing tasks with user association: {tasks_with_user}")
            logger.info(f"  (Note: Documents and tasks will have user_id set to NULL)")
            
            if user_count == 0:
                logger.info("No users found to clear.")
                return
            
            # Confirm deletion
            print(f"\n⚠️  WARNING: This will delete {user_count} users and {session_count} sessions!")
            print("   This will make the application unusable until new users are created.")
            print("   You will need to create a new admin user to access the application.")
            response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
            
            if response != 'yes':
                logger.info("Operation cancelled by user.")
                return
            
            logger.info("Starting deletion process...")
            
            # Delete in order to respect foreign key constraints
            
            # 1. Delete Sessions (required - non-nullable FK to users)
            logger.info("Deleting user sessions...")
            sessions = session.exec(select(UserSession)).all()
            for session_obj in sessions:
                session.delete(session_obj)
            logger.info(f"Deleted {len(sessions)} user sessions")
            
            # 2. Set user_id to NULL for optional relationships (nullable FKs)
            # This is handled automatically by the database, but we log it for clarity
            logger.info("Clearing user associations from documents and tasks...")
            documents_updated = session.exec(select(Document).where(Document.user_id.isnot(None))).all()
            tasks_updated = session.exec(select(ProcessingTask).where(ProcessingTask.user_id.isnot(None))).all()
            for doc in documents_updated:
                doc.user_id = None
            for task in tasks_updated:
                task.user_id = None
            logger.info(f"Cleared user associations from {len(documents_updated)} documents and {len(tasks_updated)} tasks")
            
            # 3. Delete Users
            logger.info("Deleting users...")
            users = session.exec(select(User)).all()
            for user in users:
                logger.debug(f"Deleting user: {user.username} (ID: {user.id})")
                session.delete(user)
            logger.info(f"Deleted {len(users)} users")
            
            # Commit all deletions
            session.commit()
            
            # Verify deletion
            remaining_users = len(session.exec(select(User)).all())
            remaining_sessions = len(session.exec(select(UserSession)).all())
            
            logger.info("✅ User cleanup completed successfully!")
            logger.info(f"Remaining users: {remaining_users}")
            logger.info(f"Remaining sessions: {remaining_sessions}")
            
            if remaining_users == 0:
                logger.info("🎉 All users have been cleared!")
                logger.info("⚠️  Remember to create a new admin user to access the application.")
            else:
                logger.warning(f"⚠️  {remaining_users} users still remain (this shouldn't happen)")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            session.rollback()
            raise


def main():
    """Main function."""
    print("🗑️  Backend User Cleanup Script")
    print("=" * 50)
    print(f"Database: {config.settings.database_url}")
    print(f"Environment: {config.settings.node_env_value}")
    print("=" * 50)
    
    try:
        clear_users()
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

