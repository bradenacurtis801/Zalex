#!/usr/bin/env python3
"""
Script to clear all document-related data from the database while preserving users.
This will delete all documents, classifications, feedback, OCR data, PDF cache, and upload sessions.
"""

import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from src.models.database import (
    Document,
    DocumentClassification,
    DocumentFeedback,
    OCRData,
    PDFCache,
    UploadSession,
    UploadSessionFile,
    ProcessingTask,
    EmbeddingMetadata,
    Entity,
    User
)
import config
from src.core.constants import get_database_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clear_document_data():
    """Clear all document-related data from the database."""
    
    logger.info("Starting document data cleanup...")
    
    # Create database engine
    engine = create_engine(
        config.settings.database_url,
        echo=config.LOG_LEVEL == "DEBUG",
        **get_database_config()
    )
    
    with Session(engine) as session:
        try:
            # Get counts before deletion for reporting
            document_count = len(session.exec(select(Document)).all())
            classification_count = len(session.exec(select(DocumentClassification)).all())
            feedback_count = len(session.exec(select(DocumentFeedback)).all())
            ocr_count = len(session.exec(select(OCRData)).all())
            pdf_cache_count = len(session.exec(select(PDFCache)).all())
            upload_session_count = len(session.exec(select(UploadSession)).all())
            upload_session_file_count = len(session.exec(select(UploadSessionFile)).all())
            processing_task_count = len(session.exec(select(ProcessingTask)).all())
            embedding_metadata_count = len(session.exec(select(EmbeddingMetadata)).all())
            entity_count = len(session.exec(select(Entity)).all())
            user_count = len(session.exec(select(User)).all())
            
            logger.info(f"Current data counts:")
            logger.info(f"  Documents: {document_count}")
            logger.info(f"  Classifications: {classification_count}")
            logger.info(f"  Feedback: {feedback_count}")
            logger.info(f"  OCR Data: {ocr_count}")
            logger.info(f"  PDF Cache: {pdf_cache_count}")
            logger.info(f"  Upload Sessions: {upload_session_count}")
            logger.info(f"  Upload Session Files: {upload_session_file_count}")
            logger.info(f"  Processing Tasks: {processing_task_count}")
            logger.info(f"  Embedding Metadata: {embedding_metadata_count}")
            logger.info(f"  Entities: {entity_count}")
            logger.info(f"  Users: {user_count} (will be preserved)")
            
            if document_count == 0:
                logger.info("No document data found to clear.")
                return
            
            # Confirm deletion
            print(f"\n⚠️  WARNING: This will delete {document_count} documents and all related data!")
            print("   Users will be preserved.")
            response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
            
            if response != 'yes':
                logger.info("Operation cancelled by user.")
                return
            
            logger.info("Starting deletion process...")
            
            # Delete in order to respect foreign key constraints
            
            # 1. Delete UploadSessionFiles (references documents)
            logger.info("Deleting upload session files...")
            upload_session_files = session.exec(select(UploadSessionFile)).all()
            for file in upload_session_files:
                session.delete(file)
            logger.info(f"Deleted {len(upload_session_files)} upload session files")
            
            # 2. Delete UploadSessions
            logger.info("Deleting upload sessions...")
            upload_sessions = session.exec(select(UploadSession)).all()
            for session_obj in upload_sessions:
                session.delete(session_obj)
            logger.info(f"Deleted {len(upload_sessions)} upload sessions")
            
            # 3. Delete OCRData (references documents)
            logger.info("Deleting OCR data...")
            ocr_data = session.exec(select(OCRData)).all()
            for ocr in ocr_data:
                session.delete(ocr)
            logger.info(f"Deleted {len(ocr_data)} OCR data records")
            
            # 4. Delete PDFCache (references documents)
            logger.info("Deleting PDF cache...")
            pdf_caches = session.exec(select(PDFCache)).all()
            for cache in pdf_caches:
                session.delete(cache)
            logger.info(f"Deleted {len(pdf_caches)} PDF cache records")
            
            # 5. Delete DocumentFeedback (references documents)
            logger.info("Deleting document feedback...")
            feedbacks = session.exec(select(DocumentFeedback)).all()
            for feedback in feedbacks:
                session.delete(feedback)
            logger.info(f"Deleted {len(feedbacks)} feedback records")
            
            # 6. Delete DocumentClassifications (references documents)
            logger.info("Deleting document classifications...")
            classifications = session.exec(select(DocumentClassification)).all()
            for classification in classifications:
                session.delete(classification)
            logger.info(f"Deleted {len(classifications)} classification records")
            
            # 7. Delete ProcessingTasks (references documents)
            logger.info("Deleting processing tasks...")
            processing_tasks = session.exec(select(ProcessingTask)).all()
            for task in processing_tasks:
                session.delete(task)
            logger.info(f"Deleted {len(processing_tasks)} processing task records")
            
            # 8. Delete Entities (references embedding_metadata)
            logger.info("Deleting entities...")
            entities = session.exec(select(Entity)).all()
            for entity in entities:
                session.delete(entity)
            logger.info(f"Deleted {len(entities)} entity records")
            
            # 9. Delete EmbeddingMetadata (references documents)
            logger.info("Deleting embedding metadata...")
            embedding_metadata = session.exec(select(EmbeddingMetadata)).all()
            for metadata in embedding_metadata:
                session.delete(metadata)
            logger.info(f"Deleted {len(embedding_metadata)} embedding metadata records")
            
            # 10. Finally, delete Documents
            logger.info("Deleting documents...")
            documents = session.exec(select(Document)).all()
            for document in documents:
                session.delete(document)
            logger.info(f"Deleted {len(documents)} documents")
            
            # Commit all deletions
            session.commit()
            
            # Verify deletion
            remaining_documents = len(session.exec(select(Document)).all())
            remaining_users = len(session.exec(select(User)).all())
            
            logger.info("✅ Document data cleanup completed successfully!")
            logger.info(f"Remaining documents: {remaining_documents}")
            logger.info(f"Remaining users: {remaining_users}")
            
            if remaining_documents == 0:
                logger.info("🎉 All document data has been cleared!")
            else:
                logger.warning(f"⚠️  {remaining_documents} documents still remain (this shouldn't happen)")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            session.rollback()
            raise


def main():
    """Main function."""
    print("🗑️  ScanPro Document Data Cleanup Script")
    print("=" * 50)
    print(f"Database: {config.settings.database_url}")
    print(f"Environment: {config.settings.node_env_value}")
    print("=" * 50)
    
    try:
        clear_document_data()
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
