"""Repository for User and Session data access operations."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from psycopg2.errors import UniqueViolation
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

import src.models.database as db
from src.models.database import Session as DBSession
from src.models.database import User

logger = logging.getLogger(__name__)


class DataRepository:
    """Repository for User and Session database operations."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self._db = db

    # ========== Auth Operations ==========

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        return self._db.get(User, user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            username: Username

        Returns:
            User if found, None otherwise
        """
        return self._db.exec(select(User).where(User.username == username)).first()

    def get_active_user_by_username(self, username: str) -> Optional[User]:
        """
        Get an active user by username.

        Args:
            username: Username

        Returns:
            Active User if found, None otherwise
        """
        return self._db.exec(
            select(User).where(User.username == username, User.is_active == True)
        ).first()

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of User objects
        """
        return list(
            self._db.exec(
                select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
            ).all()
        )

    def check_username_or_email_exists(
        self, username: str, email: str
    ) -> Optional[User]:
        """
        Check if a username or email already exists.

        Args:
            username: Username to check
            email: Email to check

        Returns:
            Existing User if found, None otherwise
        """
        return self._db.exec(
            select(User).where((User.username == username) | (User.email == email))
        ).first()

    def create_user(
        self,
        username: str,
        email: str,
        full_name: str,
        password_hash: str,
        user_role: str,
    ) -> User:
        """
        Create a new user.

        Args:
            username: Username
            email: Email address
            full_name: Full name
            password_hash: Hashed password
            user_role: User role

        Returns:
            Created User object
        """
        db_user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            user_role=user_role,
        )
        self._db.add(db_user)
        self._db.commit()
        self._db.refresh(db_user)
        return db_user

    def update_user(self, user: User) -> User:
        """
        Update a user record.

        Args:
            user: User object with updated fields

        Returns:
            Updated User object
        """
        user.updated_at = datetime.now(timezone.utc)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def delete_user(self, user: User) -> None:
        """
        Delete a user.

        Args:
            user: User to delete
        """
        self._db.delete(user)
        self._db.commit()
        logger.debug(f"Deleted user {user.id} ({user.username})")

    # ========== Session Operations ==========

    def create_session(
        self, user_id: int, token_hash: str, expires_at: datetime
    ) -> DBSession:
        """
        Create a new session.

        Args:
            user_id: User ID
            token_hash: Hashed session token
            expires_at: Session expiration time

        Returns:
            Created Session object
        """
        db_session = DBSession(
            user_id=user_id,
            session_token=token_hash,
            expires_at=expires_at,
        )
        self._db.add(db_session)
        self._db.commit()
        return db_session

    def get_session_by_token_hash(
        self, token_hash: str, include_revoked: bool = False
    ) -> Optional[DBSession]:
        """
        Get a session by token hash.

        Args:
            token_hash: Hashed session token
            include_revoked: Whether to include revoked sessions

        Returns:
            Session if found, None otherwise
        """
        stmt = select(DBSession).where(DBSession.session_token == token_hash)
        if not include_revoked:
            stmt = stmt.where(DBSession.is_revoked == False)
        return self._db.exec(stmt).first()

    def get_sessions_by_user_id(self, user_id: int) -> List[DBSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of Session objects
        """
        return list(
            self._db.exec(select(DBSession).where(DBSession.user_id == user_id)).all()
        )

    def revoke_all_sessions_for_user(self, user_id: int) -> int:
        """
        Revoke all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions revoked
        """
        sessions = self.get_sessions_by_user_id(user_id)
        revoked_count = 0
        for session in sessions:
            session.is_revoked = True
            self._db.add(session)
            revoked_count += 1

        if revoked_count > 0:
            self._db.commit()

        return revoked_count

    def update_session_last_activity(
        self, session: DBSession, last_activity: datetime
    ) -> DBSession:
        """
        Update session last activity timestamp.

        Args:
            session: Session to update
            last_activity: New last activity timestamp

        Returns:
            Updated Session object
        """
        session.last_activity = last_activity
        self._db.add(session)
        self._db.commit()
        return session

        #################################################
        ### ========== Category Operations ========== ###
        #################################################

    def get_category_by_name(self, name: str) -> Optional[db.Category]:
        """
        Get a category by name.

        Args:
            name: Category name

        Returns:
            Category if found, None otherwise
        """
        stmt = select(db.Category).where(db.Category.name == name)
        return self._db.exec(stmt).first()

    def get_classification(self, category_id: int) -> Optional[db.Category]:
        """
        Get a category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category if found, None otherwise
        """
        return self._db.get(db.Category, category_id)
    
    def get_all_categories(self) -> List[str]:
        """
        Get all unique categories from the database.

        Returns:
            List of unique category names
        """
        stmt = select(db.DocumentClassification.category).distinct()
        results = self._db.exec(stmt).all()

        categories = []
        for row in results:
            category = row[0] if isinstance(row, (tuple, list)) else row
            if category:
                categories.append(category)

        return sorted(list(set(categories)))
    
    def get_all_categories2(self) -> List[db.Category]:
        """
        Get all categories.

        Returns:
            List of all Category objects
        """
        stmt = select(db.Category).where(db.Category.is_active == True)
        return list(self._db.exec(stmt).all())

    def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> db.Category:
        """
        Create a new category.

        Args:
            name: Category name
            description: Category description (optional)
            created_by: User ID who created the category (optional)

        Returns:
            Created Category record
        """
        category = db.Category(
            name=name,
            description=description,
            created_by=created_by,
        )
        self._db.add(category)
        self._db.commit()
        self._db.refresh(category)
        return category

    def add_training_document_for_category(
        self,
        category_id: int,
        document_id: str,
        uploaded_by: Optional[int] = None,
    ) -> db.CategoryTrainingDocument:
        """
        Add a training document to a category.

        Args:
            category_id: Category ID
            document_id: Document ID
            uploaded_by: User ID who uploaded the document (optional)

        Returns:
            Created CategoryTrainingDocument record
        """
        training_doc = db.CategoryTrainingDocument(
            category_id=category_id,
            document_id=document_id,
            uploaded_by=uploaded_by,
        )
        self._db.add(training_doc)
        self._db.commit()
        self._db.refresh(training_doc)
        return training_doc

    def get_training_documents_from_category(self, category_id: int) -> List[db.CategoryTrainingDocument]:
        """
        Get all training documents for a category.

        Args:
            category_id: Category ID

        Returns:
            List of CategoryTrainingDocument objects
        """
        stmt = select(db.CategoryTrainingDocument).where(
            db.CategoryTrainingDocument.category_id == category_id
        )
        return list(self._db.exec(stmt).all())

    ################################################################
    ### ========== Document Classification Operations ========== ###
    ################################################################

    def create_or_update_classification(
        self,
        document_id: str,
        category: str,
        confidence: float,
        user_id: Optional[int] = None,
    ) -> db.DocumentClassification:
        """
        Create or update a DocumentClassification record using PostgreSQL UPSERT.
        This is atomic and handles race conditions efficiently.

        Args:
            document_id: Document ID (SHA256 hash)
            category: Classification category
            confidence: Confidence score (0-1)
            user_id: User ID who created/updated the classification (optional)

        Returns:
            Created or updated DocumentClassification record
        """
        # Build the insert statement
        stmt = insert(db.DocumentClassification).values(
            document_id=document_id,
            category=category,
            confidence=confidence,
            user_id=user_id,
        )
        
        # Build update dictionary for ON CONFLICT
        update_dict = {
            'category': stmt.excluded.category,
            'confidence': stmt.excluded.confidence,
        }
        if user_id is not None:
            update_dict['user_id'] = stmt.excluded.user_id
        
        # Use PostgreSQL's ON CONFLICT DO UPDATE (UPSERT)
        stmt = stmt.on_conflict_do_update(
            index_elements=['document_id'],
            set_=update_dict
        )
        
        # Execute the upsert
        self._db.execute(stmt)
        self._db.commit()
        
        # Fetch and return the updated/created record
        return self.get_classification(document_id)

    def get_classification_by_document_id(
        self, document_id: str
    ) -> Optional[db.DocumentClassification]:
        """
        Get the classification for a document (one-to-one relationship).

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            DocumentClassification record if found, None otherwise
        """
        stmt = select(db.DocumentClassification).where(
            db.DocumentClassification.document_id == document_id
        )
        return self._db.exec(stmt).first()

    def update_classification(
        self,
        classification: db.DocumentClassification,
        category: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> db.DocumentClassification:
        """
        Update a classification record.

        Args:
            classification: Classification record to update
            category: New category (optional)
            confidence: New confidence score (optional)

        Returns:
            Updated DocumentClassification record
        """
        if category is not None:
            classification.category = category
        if confidence is not None:
            classification.confidence = confidence
        classification.updated_at = datetime.now()

        self._db.add(classification)
        self._db.commit()
        self._db.refresh(classification)
        return classification

    def delete_classification(self, document_id: str) -> bool:
        """
        Delete the classification for a document (one-to-one relationship).

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            True if classification was deleted, False if not found
        """
        classification = self.get_by_document_id(document_id)
        if classification:
            self._db.delete(classification)
            self._db.commit()
            return True
        return False

    def get_category_counts(self) -> dict[str, int]:
        """
        Get document counts per category.

        Returns:
            Dictionary mapping category names to document counts
        """
        stmt = select(
            db.DocumentClassification.category, db.DocumentClassification.id
        ).distinct()
        results = self._db.exec(stmt).all()

        summary = {}
        for category, _ in results:
            summary[category] = summary.get(category, 0) + 1

        return summary

    def get_documents_by_category(
        self, category: str, skip: int = 0, limit: int = 100
    ) -> List[Tuple[db.Document, db.DocumentClassification, Optional[User]]]:
        """
        Get documents in a specific category with their classifications and users.

        Args:
            category: Category name to filter by
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (for pagination)

        Returns:
            List of tuples (Document, DocumentClassification, Optional[User])
        """
        stmt = (
            select(db.Document, db.DocumentClassification, User)
            .join(
                db.DocumentClassification,
                db.Document.id == db.DocumentClassification.document_id,
            )
            .outerjoin(User, db.DocumentClassification.user_id == User.id)
            .where(db.DocumentClassification.category == category)
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.exec(stmt).all())

    def get_document_count_by_category(self, category: str) -> int:
        """
        Get total count of documents in a specific category.

        Args:
            category: Category name to filter by

        Returns:
            Total number of documents in the category
        """
        stmt = (
            select(db.Document.id)
            .join(
                db.DocumentClassification,
                db.Document.id == db.DocumentClassification.document_id,
            )
            .where(db.DocumentClassification.category == category)
        )
        return len(list(self._db.exec(stmt).all()))

    def get_all_documents_with_classifications(
        self, skip: int = 0, limit: int = 100
    ) -> List[Tuple[db.Document, db.DocumentClassification, Optional[User]]]:
        """
        Get all documents with their classifications and users (with pagination).

        Args:
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (for pagination)

        Returns:
            List of tuples (Document, DocumentClassification, Optional[User])
        """
        stmt = (
            select(db.Document, db.DocumentClassification, User)
            .join(
                db.DocumentClassification,
                db.Document.id == db.DocumentClassification.document_id,
            )
            .outerjoin(User, db.DocumentClassification.user_id == User.id)
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.exec(stmt).all())

    def get_total_document_count_with_classifications(self) -> int:
        """
        Get total count of all documents with classifications.

        Returns:
            Total number of documents with classifications
        """
        stmt = (
            select(db.Document.id)
            .join(
                db.DocumentClassification,
                db.Document.id == db.DocumentClassification.document_id,
            )
        )
        return len(list(self._db.exec(stmt).all()))

    ##########################################################
    ### ========== Document Feedback Operations ========== ###
    ##########################################################

    def create_document_feedback(
        self,
        document_id: str,
        feedback_type: str,
        suggested_category: Optional[str] = None,
        comment: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> db.DocumentFeedback:
        """
        Create a new DocumentFeedback record.

        Args:
            document_id: Document ID (SHA256 hash)
            feedback_type: Type of feedback (e.g., "incorrect", "correct", "uncertain")
            suggested_category: Suggested category (optional)
            comment: User comment (optional)
            user_id: User ID who provided the feedback (optional)

        Returns:
            Created DocumentFeedback record
        """
        feedback = db.DocumentFeedback(
            document_id=document_id,
            feedback_type=feedback_type,
            suggested_category=suggested_category,
            comment=comment,
            user_id=user_id,
        )
        self._db.add(feedback)
        self._db.commit()
        self._db.refresh(feedback)
        return feedback

    def get_document_feedback(self, document_id: str) -> List[db.DocumentFeedback]:
        """
        Get all feedback records for a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            List of DocumentFeedback records
        """
        stmt = (
            select(db.DocumentFeedback)
            .where(db.DocumentFeedback.document_id == document_id)
            .order_by(db.DocumentFeedback.created_at.desc())
        )
        return list(self._db.exec(stmt).all())

    def get_all_document_feedback(
        self, skip: int = 0, limit: int = 100
    ) -> List[db.DocumentFeedback]:
        """
        Get all feedback records with pagination.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)

        Returns:
            List of DocumentFeedback records
        """
        stmt = (
            select(db.DocumentFeedback)
            .offset(skip)
            .limit(limit)
            .order_by(db.DocumentFeedback.created_at.desc())
        )
        return list(self._db.exec(stmt).all())

    def get_document_feedback_total_count(self) -> int:
        """
        Get total count of all feedback records.

        Returns:
            Total number of feedback records
        """
        stmt = select(db.DocumentFeedback.id)
        return len(list(self._db.exec(stmt).all()))

    def delete_document_feedback(self, document_id: str) -> int:
        """
        Delete all feedback records for a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Number of records deleted
        """
        stmt = select(db.DocumentFeedback).where(db.DocumentFeedback.document_id == document_id)
        feedback_list = list(self._db.exec(stmt).all())

        for feedback in feedback_list:
            self._db.delete(feedback)

        self._db.commit()
        return len(feedback_list)

    ##########################################################
    ### ========== Document Operations ========== ###
    ##########################################################

    def get_document(self, document_id: str) -> Optional[db.Document]:
        """
        Get a document by its ID.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Document if found, None otherwise
        """
        return self._db.get(db.Document, document_id)

    def document_exists(self, document_id: str) -> bool:
        """
        Check if a document exists.

        Args:
            document_id: Document ID

        Returns:
            True if document exists, False otherwise
        """
        document = self.get_by_id(document_id)
        return document is not None

    def create_document(
        self,
        document_id: str,
        filename: str,
        file_content: bytes,
        file_size: int,
        mime_type: str,
        user_id: Optional[int] = None,
        status: db.DocumentStatus = db.DocumentStatus.PROCESSING,
    ) -> db.Document:
        """
        Create a new document record.

        Args:
            document_id: Document ID (SHA256 hash)
            filename: Original filename
            file_content: File content as bytes
            file_size: File size in bytes
            mime_type: MIME type
            user_id: User ID who uploaded the document (optional)
            status: Document status (default: PROCESSING)

        Returns:
            Created Document record
        """
        document = db.Document(
            id=document_id,
            filename=filename,
            file_content=file_content,
            file_size=file_size,
            mime_type=mime_type,
            user_id=user_id,
            status=status,
        )
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document

    def update_document_status(
        self,
        document: db.Document,
        status: db.DocumentStatus,
    ) -> db.Document:
        """
        Update document status.

        Args:
            document: Document to update
            status: New status

        Returns:
            Updated Document record
        """
        document.status = status
        document.updated_at = datetime.now(timezone.utc)
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document

    def delete_document(
        self,
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Delete a document and all its related records.
        Handles cascading deletes for all tables that reference the document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Dict with deletion counts and success status

        Raises:
            ValueError: If document not found
        """
        # First, check if document exists
        document = self.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        deletion_counts = {
            "document": 0,
            "classifications": 0,
            "feedback": 0,
            "pdf_cache": 0,
            "upload_session_files": 0,
            "ocr_data": 0,
            "embedding_metadata": 0,
        }

        try:
            # Delete related records first (respecting foreign key constraints)
            # Order matters: delete child records before parent records

            # 1. Delete Entity records (via EmbeddingMetadata)
            metadata_stmt = select(db.EmbeddingMetadata).where(
                db.EmbeddingMetadata.document_id == document_id
            )
            metadata_list = list(self._db.exec(metadata_stmt).all())
            
            for metadata in metadata_list:
                # Delete related Entity records first
                entity_stmt = select(db.Entity).where(
                    db.Entity.embedding_metadata_id == metadata.id
                )
                entities = list(self._db.exec(entity_stmt).all())
                for entity in entities:
                    self._db.delete(entity)
                deletion_counts["embedding_metadata"] += 1
            
            # Delete EmbeddingMetadata records
            for metadata in metadata_list:
                self._db.delete(metadata)

            # 2. Delete DocumentClassifications
            classification_stmt = select(db.DocumentClassification).where(
                db.DocumentClassification.document_id == document_id
            )
            classifications = list(self._db.exec(classification_stmt).all())
            for classification in classifications:
                self._db.delete(classification)
            deletion_counts["classifications"] = len(classifications)

            # 3. Delete DocumentFeedback
            feedback_stmt = select(db.DocumentFeedback).where(
                db.DocumentFeedback.document_id == document_id
            )
            feedbacks = list(self._db.exec(feedback_stmt).all())
            for feedback in feedbacks:
                self._db.delete(feedback)
            deletion_counts["feedback"] = len(feedbacks)

            # 4. Delete PDFCache
            pdf_cache_stmt = select(db.PDFCache).where(
                db.PDFCache.document_id == document_id
            )
            pdf_cache = self._db.exec(pdf_cache_stmt).first()
            if pdf_cache:
                self._db.delete(pdf_cache)
                deletion_counts["pdf_cache"] = 1

            # 5. Delete OCRData
            ocr_stmt = select(db.OCRData).where(
                db.OCRData.document_id == document_id
            )
            ocr_records = list(self._db.exec(ocr_stmt).all())
            for ocr_record in ocr_records:
                self._db.delete(ocr_record)
            deletion_counts["ocr_data"] = len(ocr_records)

            # 6. Finally, delete the Document itself
            self._db.delete(document)
            deletion_counts["document"] = 1

            # Commit all deletions
            self._db.commit()

            logger.info(
                f"Successfully deleted document {document_id} and {sum(deletion_counts.values())} related records"
            )

            return {
                "success": True,
                "message": f"Document '{document.filename}' and all associated data deleted successfully",
                "deletion_counts": deletion_counts,
                "document_id": document_id,
            }

        except Exception as e:
            logger.error(f"Error deleting document {document_id} and related records: {e}")
            self._db.rollback()
            raise

    ################################################################
    ### ========== Document Metadata Operations ========== ###
    ################################################################

    def append_document_metadata(
        self,
        document_id: str,
        faiss_index: int,
        page_number: int,
        text: str,
        category: str = "",
        entities: List[Dict[str, Any]] = None,
    ) -> None:
        """
        Append metadata for a document to the database.
        Should be called after adding embedding to FAISS to maintain index alignment.
        
        Args:
            document_id: Document ID (file hash)
            faiss_index: Position in FAISS index
            page_number: Page number
            text: The text content
            category: Document classification category
            entities: List of extracted named entities
        """
        # Convert entities to JSON string
        entities_json = json.dumps(entities or [], ensure_ascii=False)
        
        metadata = db.EmbeddingMetadata(
            document_id=document_id,
            faiss_index=faiss_index,
            page_number=page_number,
            text=text,
            category=category,
            entities=entities_json,
        )
        self._db.add(metadata)
        self._db.commit()
        logger.debug(f"Added metadata for document {document_id}, FAISS index {faiss_index}, page {page_number}")
    
    def get_document_metadata_from_index(self, faiss_index: int) -> Optional[db.EmbeddingMetadata]:
        """
        Get metadata by FAISS index position.
        
        Args:
            faiss_index: Index position in FAISS
            
        Returns:
            EmbeddingMetadata if found, None otherwise
        """
        stmt = select(db.EmbeddingMetadata).where(db.EmbeddingMetadata.faiss_index == faiss_index)
        return self._db.exec(stmt).first()
    
    def get_document_metadata_by_document_id(self, document_id: str) -> List[db.EmbeddingMetadata]:
        """
        Get all metadata for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of metadata entries for the document
        """
        stmt = select(db.EmbeddingMetadata).where(db.EmbeddingMetadata.document_id == document_id)
        return list(self._db.exec(stmt).all())
    
    def get_all_document_metadata(self) -> List[db.EmbeddingMetadata]:
        """Get all metadata."""
        stmt = select(db.EmbeddingMetadata)
        return list(self._db.exec(stmt).all())

    def get_document_metadata_from_indices(self, faiss_indices: List[int]) -> List[db.EmbeddingMetadata]:
        """
        Get metadata by multiple FAISS index positions.
        Also loads associated Entity records using eager loading.
        
        Args:
            faiss_indices: List of FAISS index positions
            
        Returns:
            List of EmbeddingMetadata records with entities loaded via relationship
        """
        if not faiss_indices:
            return []
        
        # Use selectinload to eagerly load entities in one query instead of N+1 queries
        stmt = (
            select(db.EmbeddingMetadata)
            .where(db.EmbeddingMetadata.faiss_index.in_(faiss_indices))
            .options(selectinload(db.EmbeddingMetadata.entities))
        )
        metadata_list = list(self._db.exec(stmt).all())
        
        # Entities are now loaded via the relationship, accessible as metadata.entities
        return metadata_list

    def get_entities(self, metadata: db.EmbeddingMetadata) -> List[Dict[str, Any]]:
        """
        Parse entities JSON string to list (legacy method for backward compatibility).
        For new code, use metadata.entities relationship directly.
        
        Args:
            metadata: EmbeddingMetadata object
            
        Returns:
            List of entity dictionaries
        """
        try:
            return json.loads(metadata.entities) if metadata.entities else []
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse entities JSON for metadata ID {metadata.id}")
            return []

    def delete_document_metadata(self, document_id: str) -> int:
        """
        Delete all EmbeddingMetadata records (and their related Entity records) for a document.
        
        Args:
            document_id: Document ID (SHA256 hash)
            
        Returns:
            Number of metadata records deleted
        """
        # Get all metadata records for this document
        metadata_list = self.get_by_document_id(document_id)
        
        deleted_count = 0
        for metadata in metadata_list:
            # Delete related Entity records first
            entity_stmt = select(db.Entity).where(
                db.Entity.embedding_metadata_id == metadata.id
            )
            entities = list(self._db.exec(entity_stmt).all())
            for entity in entities:
                self._db.delete(entity)
            
            # Delete the metadata record
            self._db.delete(metadata)
            deleted_count += 1
        
        if deleted_count > 0:
            self._db.commit()
        
        return deleted_count

    #####################################################
    ### ========== Document Ocr Operations ========== ###
    #####################################################

    def create_ocr_entry(
        self,
        document_id: str,
        page_number: int,
        full_text: str,
        words_data: str,
        lines_data: str,
        confidence_score: float,
        total_words: int,
        total_lines: int,
        original_image_width: Optional[int] = None,
        original_image_height: Optional[int] = None,
    ) -> db.OCRData:
        """
        Create a new OCRData record.

        Args:
            document_id: Document ID (SHA256 hash)
            page_number: Page number (0-indexed)
            full_text: Full extracted text
            words_data: JSON string of words data
            lines_data: JSON string of lines data
            confidence_score: Average confidence score (0-1)
            total_words: Total number of words
            total_lines: Total number of lines
            original_image_width: Original image width (optional)
            original_image_height: Original image height (optional)

        Returns:
            Created OCRData record
        """
        ocr_data = db.OCRData(
            document_id=document_id,
            page_number=page_number,
            full_text=full_text,
            words_data=words_data,
            lines_data=lines_data,
            confidence_score=confidence_score,
            total_words=total_words,
            total_lines=total_lines,
            original_image_width=original_image_width,
            original_image_height=original_image_height,
        )
        self._db.add(ocr_data)
        self._db.commit()
        self._db.refresh(ocr_data)
        return ocr_data

    def get_ocr_data(self, document_id: str) -> List[db.OCRData]:
        """
        Get all OCR data for a document, ordered by page number.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            List of OCRData records
        """
        stmt = (
            select(db.OCRData)
            .where(db.OCRData.document_id == document_id)
            .order_by(db.OCRData.page_number)
        )
        return list(self._db.exec(stmt).all())

    def get_ocr_entry_by_page(
        self, document_id: str, page_number: int
    ) -> Optional[db.OCRData]:
        """
        Get OCR data for a specific page of a document.

        Args:
            document_id: Document ID (SHA256 hash)
            page_number: Page number (0-indexed)

        Returns:
            OCRData record if found, None otherwise
        """
        stmt = select(db.OCRData).where(
            db.OCRData.document_id == document_id,
            db.OCRData.page_number == page_number,
        )
        return self._db.exec(stmt).first()

    def delete_ocr_entry(self, document_id: str) -> int:
        """
        Delete all OCR data for a document.

        Args:
            document_id: Document ID (SHA256 hash)

        Returns:
            Number of records deleted
        """
        stmt = select(db.OCRData).where(db.OCRData.document_id == document_id)
        ocr_data_list = list(self._db.exec(stmt).all())

        for ocr_data in ocr_data_list:
            self._db.delete(ocr_data)

        self._db.commit()
        return len(ocr_data_list)

    ###########################################################
    ### ========== Document PDF Cache Operations ========== ###
    ###########################################################

    def get_pdf_cache(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve PDF cache data for a document if it exists and is not expired.

        Args:
            document_id: Document ID

        Returns:
            Cached data dictionary or None if not found/expired
        """
        try:
            # Use 0 as a sentinel value to represent "all pages"
            stmt = select(db.PDFCache).where(
                db.PDFCache.document_id == document_id,
                db.PDFCache.max_pages == 0
            )
            cache_record = self._db.exec(stmt).first()

            if not cache_record:
                return None

            # Check if cache is expired
            current_time = datetime.now(timezone.utc)
            expires_at = cache_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if current_time > expires_at:
                logger.debug(f"Cache expired for document {document_id}")
                # Delete expired cache record
                self._db.delete(cache_record)
                self._db.commit()
                return None

            logger.debug(f"Cache hit for document {document_id}")
            return json.loads(cache_record.pages_data)

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error reading cache for document {document_id}: {e}")
            return None

    def upsert_pdf_cache(self, document_id: str, data: Dict[str, Any], ttl_hours: int = 24) -> None:
        """
        Upsert (insert or update) PDF cache data.
        Handles race conditions with retry logic.

        Args:
            document_id: Document ID
            data: Data to cache
            ttl_hours: Time to live in hours (default: 24)
        """
        try:
            # Try to find existing cache
            stmt = select(db.PDFCache).where(
                db.PDFCache.document_id == document_id,
                db.PDFCache.max_pages == 0
            )
            existing_cache = self._db.exec(stmt).first()

            if existing_cache:
                # Update existing cache
                existing_cache.total_pages = data.get("total_pages", 0)
                existing_cache.pages_data = json.dumps(data)
                existing_cache.expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
                self._db.add(existing_cache)
            else:
                # Create new cache record
                cache_record = db.PDFCache(
                    document_id=document_id,
                    max_pages=0,  # Use 0 to represent "all pages"
                    total_pages=data.get("total_pages", 0),
                    pages_data=json.dumps(data),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
                )
                self._db.add(cache_record)

            self._db.commit()
            logger.debug(f"Cached PDF data for document {document_id}")

        except IntegrityError as e:
            # Handle race condition: if UniqueViolation, retry with update
            if isinstance(e.orig, UniqueViolation) or "UniqueViolation" in str(e) or "duplicate key" in str(e).lower():
                logger.debug(f"Cache entry already exists for {document_id}, updating instead")
                self._db.rollback()
                self._update_existing(document_id, data, ttl_hours)
            else:
                logger.warning(f"Error saving cache for document {document_id}: {e}")
                self._db.rollback()
                raise
        except Exception as e:
            logger.warning(f"Error saving cache for document {document_id}: {e}")
            self._db.rollback()
            raise

    def _update_existing(self, document_id: str, data: Dict[str, Any], ttl_hours: int) -> None:
        """
        Update existing cache record (used for retry after UniqueViolation).

        Args:
            document_id: Document ID
            data: Data to cache
            ttl_hours: Time to live in hours
        """
        try:
            stmt = select(db.PDFCache).where(
                db.PDFCache.document_id == document_id
            )
            existing_cache = self._db.exec(stmt).first()
            if existing_cache:
                existing_cache.max_pages = 0
                existing_cache.total_pages = data.get("total_pages", 0)
                existing_cache.pages_data = json.dumps(data)
                existing_cache.expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
                self._db.add(existing_cache)
                self._db.commit()
                logger.debug(f"Updated cached PDF data for document {document_id}")
            else:
                logger.warning(f"Cache entry not found after UniqueViolation for {document_id}")
        except Exception as retry_error:
            logger.warning(f"Error updating cache for document {document_id}: {retry_error}")
            self._db.rollback()
            raise

    def delete_expired_pdf_cache(self) -> int:
        """
        Delete all expired cache records.

        Returns:
            Number of records deleted
        """
        cleaned_count = 0
        current_time = datetime.now(timezone.utc)

        try:
            stmt = select(db.PDFCache).where(
                db.PDFCache.expires_at < current_time
            )
            expired_records = self._db.exec(stmt).all()

            for record in expired_records:
                self._db.delete(record)
                cleaned_count += 1
                logger.debug(f"Cleaned up expired cache record for document {record.document_id}")

            self._db.commit()

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            self._db.rollback()

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired cache records")

        return cleaned_count

    def get_pdf_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            stmt = select(db.PDFCache)
            cache_records = self._db.exec(stmt).all()
            
            total_records = len(cache_records)
            total_size = sum(len(record.pages_data) for record in cache_records)

            return {
                "total_records": total_records,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "ttl_hours": 24,
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    def delete_pdf_cache(self, document_id: str) -> bool:
        """
        Delete cache record for a specific document.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(db.PDFCache).where(
                db.PDFCache.document_id == document_id
            )
            cache_record = self._db.exec(stmt).first()
            
            if cache_record:
                self._db.delete(cache_record)
                self._db.commit()
                logger.debug(f"Deleted cache for document {document_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cache for document {document_id}: {e}")
            self._db.rollback()
            return False

    ###########################################################
    ### ========== Document Tasks Operations ========== ###
    ###########################################################

    def get_task(self, task_id: int) -> Optional[db.ProcessingTask]:
        """
        Get a processing task by its ID.

        Args:
            task_id: Task ID

        Returns:
            ProcessingTask if found, None otherwise
        """
        return self._db.get(db.ProcessingTask, task_id)

    def get_pending_task(self, document_id: str) -> Optional[db.ProcessingTask]:
        """
        Get a pending task for a document.

        Args:
            document_id: Document ID

        Returns:
            Pending ProcessingTask if found, None otherwise
        """
        stmt = (
            select(db.ProcessingTask)
            .where(db.ProcessingTask.document_id == document_id)
            .where(db.ProcessingTask.status == db.ProcessingTaskStatus.PENDING)
        )
        return self._db.exec(stmt).first()

    def get_all_pending_tasks(self) -> List[db.ProcessingTask]:
        """
        Get all pending tasks.

        Returns:
            List of pending ProcessingTask objects
        """
        stmt = select(db.ProcessingTask).where(
            db.ProcessingTask.status == db.ProcessingTaskStatus.PENDING
        )
        return list(self._db.exec(stmt).all())

    def get_all_processing_tasks(self) -> List[db.ProcessingTask]:
        """
        Get all tasks in PROCESSING status.

        Returns:
            List of ProcessingTask objects in PROCESSING status
        """
        stmt = select(db.ProcessingTask).where(
            db.ProcessingTask.status == db.ProcessingTaskStatus.PROCESSING
        )
        return list(self._db.exec(stmt).all())

    def create_task(
        self,
        document_id: str,
        filename: str,
        user_id: Optional[int] = None,
        status: db.ProcessingTaskStatus = db.ProcessingTaskStatus.PENDING,
    ) -> db.ProcessingTask:
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
        task = db.ProcessingTask(
            document_id=document_id,
            filename=filename,
            user_id=user_id,
            status=status,
        )
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    def update_task_status(
        self,
        task: db.ProcessingTask,
        status: db.ProcessingTaskStatus,
        error: Optional[str] = None,
    ) -> db.ProcessingTask:
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

    def reset_processing_tasks_to_pending(self, tasks: List[db.ProcessingTask]) -> None:
        """
        Reset tasks from PROCESSING to PENDING status.

        Args:
            tasks: List of tasks to reset
        """
        for task in tasks:
            task.status = db.ProcessingTaskStatus.PENDING
            task.error = None
            task.updated_at = datetime.now(timezone.utc)
            self._db.add(task)
        self._db.commit()

    def delete_task_by_obj(self, task: db.ProcessingTask) -> None:
        """
        Delete a processing task.

        Args:
            task: The processing task to delete
        """
        self._db.delete(task)
        self._db.commit()
        logger.debug(f"Deleted processing task {task.id} for document {task.document_id}")

    def delete_task(self, task_id: int) -> bool:
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

    def delete_tasks(self, task_ids: List[int]) -> int:
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
        stmt = select(db.ProcessingTask).where(
            db.ProcessingTask.id.in_(task_ids)
        )
        tasks_to_delete = list(self._db.exec(stmt).all())
        
        # Delete all tasks
        for task in tasks_to_delete:
            self._db.delete(task)
        
        self._db.commit()
        deleted_count = len(tasks_to_delete)
        logger.debug(f"Deleted {deleted_count} processing task(s)")
        return deleted_count

    def get_all_tasks_by_user_id(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> tuple[List[db.ProcessingTask], int]:
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
        count_stmt = select(func.count(db.ProcessingTask.id)).where(
            db.ProcessingTask.user_id == user_id
        )
        total_count = self._db.exec(count_stmt).one()
        
        # Get paginated results
        stmt = (
            select(db.ProcessingTask)
            .where(db.ProcessingTask.user_id == user_id)
            .order_by(db.ProcessingTask.created_at.desc())
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
        total_stmt = select(func.count(db.ProcessingTask.id)).where(
            db.ProcessingTask.user_id == user_id
        )
        total = self._db.exec(total_stmt).one()
        
        # Count by status
        pending_stmt = select(func.count(db.ProcessingTask.id)).where(
            db.ProcessingTask.user_id == user_id,
            db.ProcessingTask.status == db.ProcessingTaskStatus.PENDING
        )
        pending = self._db.exec(pending_stmt).one()
        
        processing_stmt = select(func.count(db.ProcessingTask.id)).where(
            db.ProcessingTask.user_id == user_id,
            db.ProcessingTask.status == db.ProcessingTaskStatus.PROCESSING
        )
        processing = self._db.exec(processing_stmt).one()
        
        completed_stmt = select(func.count(db.ProcessingTask.id)).where(
            db.ProcessingTask.user_id == user_id,
            db.ProcessingTask.status == db.ProcessingTaskStatus.COMPLETED
        )
        completed = self._db.exec(completed_stmt).one()
        
        failed_stmt = select(func.count(db.ProcessingTask.id)).where(
            db.ProcessingTask.user_id == user_id,
            db.ProcessingTask.status == db.ProcessingTaskStatus.FAILED
        )
        failed = self._db.exec(failed_stmt).one()
        
        return {
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed
        }