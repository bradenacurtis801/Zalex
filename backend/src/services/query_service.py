"""Query service for handling search operations."""

import logging
from typing import List, Optional

from src.ml.faiss.embeddings import EmbeddingsIndex, EmbeddingMetadata
from src.models.schemas.query import QueryResponse, SearchResult

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling document search queries."""

    def __init__(self, embeddings_index: Optional[EmbeddingsIndex]):
        self.embeddings_index = embeddings_index

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

        if not self.embeddings_index:
            logger.debug("No embeddings index available, returning empty results")
            return QueryResponse(results=[])

        try:
            # Search the index using EmbeddingsIndex
            metadata_list, distances = self.embeddings_index.search_with_metadata_and_distances(
                query_text, k
            )

            # Process results
            results = self._process_search_results(metadata_list, distances)

            logger.info(f"Found {len(results)} relevant chunks for query.")
            return QueryResponse(results=results)

        except Exception as e:
            logger.error(f"Error during query processing: {e}", exc_info=True)
            raise

    def _process_search_results(
        self, metadata_list: List[EmbeddingMetadata], distances: List[float]
    ) -> List[SearchResult]:
        """Process search results and convert to SearchResult objects."""
        results = []

        logger.debug(f"Processing {len(metadata_list)} search results")

        for i, metadata in enumerate(metadata_list):
            distance = distances[i] if i < len(distances) else None
            
            result = SearchResult(
                text=metadata.text,
                source=metadata.document_id,
                page=metadata.page_number,
                score=distance,
            )
            results.append(result)
            score_str = f"{result.score:.4f}" if result.score is not None else "None"
            logger.debug(
                f"Result {i+1}: source='{result.source}', page={result.page}, "
                f"score={score_str}, "
                f"text_preview='{result.text[:50]}...'"
            )

        logger.debug(f"Returning {len(results)} results to client")
        return results
