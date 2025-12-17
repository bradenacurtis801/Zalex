"""Query service for handling search operations."""

import logging
from typing import Any, Dict, List, Optional

from src.ml.faiss.embeddings import EmbeddingsIndex
from src.models.database import EmbeddingMetadata
from src.models.database import Entity as DBEntity
from src.models.schemas.query import Entity, QueryResponse, SearchResult
from src.repositories import DataRepository

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling document search queries."""

    def __init__(
        self,
        embeddings_index: EmbeddingsIndex,
        data_repo: DataRepository,
    ):
        self._embeddings_index = embeddings_index
        self._data_repo = data_repo

    def search_documents(self, query_text: str, k: int = 100) -> QueryResponse:
        """
        Search for documents based on query text.

        Args:
            query_text: The search query
            k: Number of results to retrieve (default: 100, capped at index size)

        Returns:
            QueryResponse with search results
        """
        logger.info(f"Processing search query: '{query_text}'")
        logger.debug(f"Query length: {len(query_text)} characters")

        if not self._embeddings_index:
            logger.warning("No embeddings index available, returning empty results")
            return QueryResponse(results=[])

        # Check if index has any embeddings
        index_size = self._embeddings_index.embeddings.ntotal
        logger.info(f"FAISS index contains {index_size} embeddings")
        
        if index_size == 0:
            logger.warning("FAISS index is empty - no documents have been indexed yet")
            return QueryResponse(results=[])

        # Cap k to not exceed the index size
        original_k = k
        k = min(k, index_size)
        if original_k > index_size:
            logger.debug(f"Capped k from {original_k} to {k} (index size: {index_size})")

        # Search the index using EmbeddingsIndex (embeddings only)
        # Get FAISS indices and distances
        distances, indices = self._search_faiss(query_text, k)
        logger.info(f"FAISS search returned {len(indices)} candidate results")
        
        # Get metadata from database using FAISS indices
        metadata_list = self._data_repo.get_document_metadata_from_indices(indices)

        logger.info(f"Found {len(metadata_list)} metadata records in database")

        # Process results
        results = self._process_search_results(metadata_list, distances, query_text)

        logger.info(f"Found {len(results)} relevant chunks for query (after filtering).")
        return QueryResponse(results=results)


    def _search_faiss(self, query_text: str, k: int):
        """
        Search FAISS index and return indices and distances.
        
        Args:
            query_text: Query text
            k: Number of results
            
        Returns:
            Tuple of (distances, indices) from FAISS search
            distances: List of floats
            indices: List of ints (converted from numpy array)
        """
        if not self._embeddings_index or self._embeddings_index.embeddings.ntotal == 0:
            return [], []
        
        # Generate embedding for query
        embedded_query = self._embeddings_index.transformer.encode([query_text], convert_to_tensor=False)
        embedded_query = embedded_query.astype('float32')
        
        # Search in FAISS index
        distances, indices = self._embeddings_index.embeddings.search(embedded_query, k)
        
        # Convert numpy arrays to Python lists with native types for database compatibility
        distances_list = distances[0].tolist() if hasattr(distances[0], 'tolist') else list(distances[0])
        indices_array = indices[0]
        
        # Filter out invalid indices (-1 values indicate no match found)
        # This happens when k is larger than the number of vectors in the index
        valid_mask = indices_array != -1
        valid_indices = indices_array[valid_mask]
        valid_distances = distances[0][valid_mask]
        
        # Convert to Python lists
        indices_list = [int(idx) for idx in valid_indices]
        distances_list = valid_distances.tolist() if hasattr(valid_distances, 'tolist') else list(valid_distances)
        
        logger.debug(f"FAISS search: requested k={k}, found {len(indices_list)} valid results (filtered {len(indices_array) - len(indices_list)} invalid -1 indices)")
        
        return distances_list, indices_list
    

    def _process_search_results(
        self, metadata_list: List[EmbeddingMetadata], distances: List[float], query_text: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Process search results.
        
        Note: We don't apply strict keyword filtering for semantic search, as the whole point
        of semantic search is to find semantically similar content even if exact words don't match.
        This is especially important for cross-language searches (e.g., searching "birth" in Spanish documents).
        
        Filters out results with empty entities lists.
        """
        results = []

        logger.debug(f"Processing {len(metadata_list)} search results")

        for i, metadata in enumerate(metadata_list):
            distance = distances[i] if i < len(distances) else None
            
            # Convert entities from database models to schema objects
            entities = self._convert_entities_to_schema(metadata.entities)
            
            # Filter out results with no entities
            if not entities:
                logger.debug(
                    f"Skipping result: source='{metadata.document_id}', page={metadata.page_number} "
                    f"(no entities found)"
                )
                continue
            
            result = SearchResult(
                text=metadata.text,
                source=metadata.document_id,
                page=metadata.page_number,
                score=distance,
                entities=entities,
            )
            results.append(result)
            score_str = f"{result.score:.4f}" if result.score is not None else "None"
            logger.debug(
                f"Result {len(results)}: source='{result.source}', page={result.page}, "
                f"score={score_str}, "
                f"text_preview='{result.text[:50]}...'"
            )

        logger.debug(f"Returning {len(results)} results to client (filtered from {len(metadata_list)} total)")
        return results
    
    def _convert_entities_to_schema(self, entities: List[DBEntity]) -> List[Entity]:
        """
        Convert Entity database models to Pydantic schema objects.
        
        Args:
            entities: List of Entity database objects
            
        Returns:
            List of Entity schema objects
        """
        if not entities:
            return []
        
        return [
            Entity(
                text=entity.text,
                label=entity.label,
                start=entity.start,
                end=entity.end,
                confidence=entity.confidence,
            )
            for entity in entities
        ]
