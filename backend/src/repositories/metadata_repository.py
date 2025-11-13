"""
Metadata storage for FAISS embeddings.
Stores metadata in the database, linked to FAISS index by position.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from src.models.database import EmbeddingMetadata as DBEmbeddingMetadata, Entity as DBEntity

logger = logging.getLogger(__name__)


class MetadataRepository:
    """
    Stores metadata for FAISS embeddings in the database.
    Metadata is linked to FAISS indices by position (faiss_index field).
    """
    
    def __init__(self, db: Session):
        """
        Initialize metadata store.
        
        Args:
            db: Database session
        """
        self._db = db
    
    def append(
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
        
        metadata = DBEmbeddingMetadata(
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
    
    def get(self, faiss_index: int) -> Optional[DBEmbeddingMetadata]:
        """
        Get metadata by FAISS index position.
        
        Args:
            faiss_index: Index position in FAISS
            
        Returns:
            DBEmbeddingMetadata if found, None otherwise
        """
        stmt = select(DBEmbeddingMetadata).where(DBEmbeddingMetadata.faiss_index == faiss_index)
        return self._db.exec(stmt).first()
    
    def get_by_document_id(self, document_id: str) -> List[DBEmbeddingMetadata]:
        """
        Get all metadata for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of metadata entries for the document
        """
        stmt = select(DBEmbeddingMetadata).where(DBEmbeddingMetadata.document_id == document_id)
        return list(self._db.exec(stmt).all())
    
    def get_all(self) -> List[DBEmbeddingMetadata]:
        """Get all metadata."""
        stmt = select(DBEmbeddingMetadata)
        return list(self._db.exec(stmt).all())

    def get_by_faiss_indices(self, faiss_indices: List[int]) -> List[DBEmbeddingMetadata]:
        """
        Get metadata by multiple FAISS index positions.
        Also loads associated Entity records.
        
        Args:
            faiss_indices: List of FAISS index positions
            
        Returns:
            List of DBEmbeddingMetadata records with entities loaded
        """
        if not faiss_indices:
            return []
        
        stmt = select(DBEmbeddingMetadata).where(
            DBEmbeddingMetadata.faiss_index.in_(faiss_indices)
        )
        metadata_list = list(self._db.exec(stmt).all())
        
        # Load entities for each metadata record
        for metadata in metadata_list:
            entity_stmt = select(DBEntity).where(
                DBEntity.embedding_metadata_id == metadata.id
            )
            metadata.entities = list(self._db.exec(entity_stmt).all())
        
        return metadata_list

    def get_entities(self, metadata: DBEmbeddingMetadata) -> List[Dict[str, Any]]:
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

    def delete_by_document_id(self, document_id: str) -> int:
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
            entity_stmt = select(DBEntity).where(
                DBEntity.embedding_metadata_id == metadata.id
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

