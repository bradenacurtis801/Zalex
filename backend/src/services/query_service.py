"""Query service for handling search operations."""

import numpy as np
import logging
from typing import List, Optional
from app_state import get_app_state
from src.models.query import QueryResponse, SearchResult

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling document search queries."""
    
    def __init__(self):
        self.app_state = get_app_state()
    
    def search_documents(self, query_text: str, k: int = 5000) -> QueryResponse:
        """
        Search for documents based on query text.
        
        Args:
            query_text: The search query
            k: Number of results to retrieve
            
        Returns:
            QueryResponse with search results
        """
        logger.info(f"Processing search query: '{query_text}'")
        logger.debug(f"Query length: {len(query_text)} characters")
        
        # Get app state components
        index = self.app_state.index
        metadata = self.app_state.metadata
        model = self.app_state.model
        
        logger.debug(f"Index status: {'Available' if index else 'None'}")
        logger.debug(f"Index total entries: {index.ntotal if index else 0}")
        logger.debug(f"Metadata entries: {len(metadata) if metadata else 0}")
        logger.debug(f"Model status: {'Available' if model else 'None'}")
        
        if not index or index.ntotal == 0:
            logger.debug("No index available or empty index, returning empty results")
            return QueryResponse(results=[])
        
        try:
            # Create query embedding
            query_embedding = self._create_query_embedding(query_text, model)
            
            # Search the index
            distances, indices = self._search_index(index, query_embedding, k)
            
            # Process results
            results = self._process_search_results(distances, indices, metadata)
            
            logger.info(f"Found {len(results)} relevant chunks for query.")
            return QueryResponse(results=results)
            
        except Exception as e:
            logger.error(f"Error during query processing: {e}", exc_info=True)
            raise
    
    def _create_query_embedding(self, query_text: str, model) -> np.ndarray:
        """Create embedding for the query text."""
        logger.debug("Creating query embedding...")
        query_embedding = model.encode([query_text])
        logger.debug(f"Query embedding shape: {query_embedding.shape}")
        logger.debug(f"Query embedding sample (first 5 values): {query_embedding[0][:5]}")
        return query_embedding
    
    def _search_index(self, index, query_embedding: np.ndarray, k: int) -> tuple:
        """Search the FAISS index for similar documents."""
        logger.debug(f"Searching FAISS index with k={k}")
        distances, indices = index.search(np.array(query_embedding).astype('float32'), k)
        logger.debug(f"Search returned {len(indices[0])} indices")
        logger.debug(f"Distance range: {distances[0].min():.4f} to {distances[0].max():.4f}")
        return distances, indices
    
    def _process_search_results(self, distances: np.ndarray, indices: np.ndarray, metadata: List[dict]) -> List[SearchResult]:
        """Process search results and convert to SearchResult objects."""
        results = []
        
        # Filter out results with -1 index (placeholder in FAISS)
        valid_indices = [i for i in indices[0] if i != -1]
        logger.debug(f"Valid indices after filtering: {len(valid_indices)}")
        
        for i, idx in enumerate(valid_indices):
            if idx < len(metadata):
                result = SearchResult(
                    text=metadata[idx].get('text', ''),
                    source=metadata[idx].get('source', ''),
                    page=metadata[idx].get('page', 0),
                    score=float(distances[0][i]) if i < len(distances[0]) else None
                )
                results.append(result)
                logger.debug(f"Result {i+1}: source='{result.source}', page={result.page}, score={result.score:.4f}, text_preview='{result.text[:50]}...'")
            else:
                logger.debug(f"Skipping invalid index {idx} (beyond metadata length {len(metadata)})")
        
        logger.debug(f"Returning {len(results)} results to client")
        return results
