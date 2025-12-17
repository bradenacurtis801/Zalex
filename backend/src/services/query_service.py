"""Query service for handling search operations."""

import logging
from typing import Any, Dict, List, Optional, Set

from src.ml.faiss.embeddings import EmbeddingsIndex
from src.models.database import EmbeddingMetadata
from src.models.database import Entity as DBEntity
from src.models.schemas.query import Entity, QueryResponse, SearchResult, QueryFilters
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

    def search_documents(
        self, 
        query_text: str = "", 
        k: int = 100, 
        filter: Optional[QueryFilters] = None
    ) -> QueryResponse:
        """
        Search for documents based on query text and filters.

        Args:
            query_text: The search query
            k: Number of results to retrieve (default: 100, capped at index size)
            filters: Optional structured filters

        Returns:
            QueryResponse with search results
        """
        logger.info(f"Processing search query: '{query_text}' filters={filter}")
        logger.debug(f"Query length: {len(query_text)} characters")

        # Early return if no index
        if not self._embeddings_index:
            logger.warning("No embeddings index available")
            return QueryResponse(results=[])

        index_size = self._embeddings_index.embeddings.ntotal
        logger.info(f"FAISS index contains {index_size} embeddings")
        
        if index_size == 0:
            logger.warning("FAISS index is empty - no documents indexed yet")
            return QueryResponse(results=[])

        # Cap k to index size
        k = min(k, index_size)
        
        # Apply filters to get candidate indices
        candidate_indices = self._apply_filter(filter) if filter else None
        
        # Handle filter-only queries (no semantic search)
        if not query_text and candidate_indices is not None:
            return self._return_filtered_results(candidate_indices)
        
        # Perform semantic search
        distances, indices = self._search_faiss(query_text, k)
        logger.info(f"FAISS search returned {len(indices)} candidates")
        
        # Intersect with filter results if present
        if candidate_indices is not None:
            indices, distances = self._filter_search_results(
                indices, distances, candidate_indices
            )
        
        # Get metadata and process results
        metadata_list = self._data_repo.get_document_metadata_from_indices(indices)
        logger.info(f"Found {len(metadata_list)} metadata records")
        
        results = self._process_search_results(metadata_list, distances, query_text)
        logger.info(f"Returning {len(results)} results")
        
        return QueryResponse(results=results)

    def _apply_filter(self, filter: QueryFilters) -> Optional[Set[int]]:
        """Apply all filters and return intersection of matching document indices."""
        candidate_sets = []
        
        # Entity filters
        if filter.entity_filter:
            for ef in filter.entity_filter:
                indices = self._data_repo.get_document_metadata_indices_by_entity_text(
                    ef.label, ef.text, match=ef.match
                )
                candidate_sets.append(set(indices))
        
        # Date range filter
        if filter.date_from and filter.date_to:
            indices = self._data_repo.get_document_metadata_indices_by_date_range(
                filter.date_from.isoformat(), 
                filter.date_to.isoformat()
            )
            candidate_sets.append(set(indices))
        
        # Category filters
        if filter.category_filter:
            cat_indices = set()
            for category in filter.category_filter:
                indices = self._data_repo.get_document_metadata_indices_by_filters(
                    category=category
                )
                cat_indices.update(indices)
            candidate_sets.append(cat_indices)
        
        # Return intersection of all filter results
        if not candidate_sets:
            return None
        
        return set.intersection(*candidate_sets) if len(candidate_sets) > 1 else candidate_sets[0]

    def _filter_search_results(
        self, 
        indices: List[int], 
        distances: List[float], 
        allowed_indices: Set[int]
    ) -> tuple[List[int], List[float]]:
        """Filter search results to only include allowed indices."""
        filtered_indices = []
        filtered_distances = []
        
        for idx, dist in zip(indices, distances):
            if idx in allowed_indices:
                filtered_indices.append(idx)
                filtered_distances.append(dist)
        
        return filtered_indices, filtered_distances

    def _return_filtered_results(self, indices: Set[int]) -> QueryResponse:
        """Return results from filter-only query (no semantic search)."""
        indices_list = list(indices)
        logger.info(f"Returning {len(indices_list)} filter-only results")
        
        metadata_list = self._data_repo.get_document_metadata_from_indices(indices_list)
        distances = [None] * len(indices_list)
        results = self._process_search_results(metadata_list, distances, query_text="")
        
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
