from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
import logging
from app_state import get_app_state
from src.models.query import QueryRequest, QueryResponse, SearchResult

logger = logging.getLogger(__name__)
router = APIRouter()
app_state = get_app_state()

@router.post("/query", response_model=QueryResponse)
async def query_index(request: QueryRequest):
    """Handles user queries, searches the index, and returns relevant results."""
    query_text = request.query
    logger.info(f"Received query: '{query_text}'")
    logger.debug(f"Query length: {len(query_text)} characters")

    # Get app state directly
    index = app_state.index
    metadata = app_state.metadata
    model = app_state.model
    
    logger.debug(f"Index status: {'Available' if index else 'None'}")
    logger.debug(f"Index total entries: {index.ntotal if index else 0}")
    logger.debug(f"Metadata entries: {len(metadata) if metadata else 0}")
    logger.debug(f"Model status: {'Available' if model else 'None'}")
    
    if not index or index.ntotal == 0:
        logger.debug("No index available or empty index, returning empty results")
        return QueryResponse(results=[])

    try:
        # Create an embedding for the query
        logger.debug("Creating query embedding...")
        query_embedding = model.encode([query_text])
        logger.debug(f"Query embedding shape: {query_embedding.shape}")
        logger.debug(f"Query embedding sample (first 5 values): {query_embedding[0][:5]}")

        # Search the FAISS index for the top 5 most similar chunks
        k = 5000  # Number of results to retrieve
        logger.debug(f"Searching FAISS index with k={k}")
        distances, indices = index.search(np.array(query_embedding).astype('float32'), k)
        logger.debug(f"Search returned {len(indices[0])} indices")
        logger.debug(f"Distance range: {distances[0].min():.4f} to {distances[0].max():.4f}")

        results = []
        # Filter out results with -1 index (placeholder in FAISS)
        valid_indices = [i for i in indices[0] if i != -1]
        logger.debug(f"Valid indices after filtering: {len(valid_indices)}")

        for i, idx in enumerate(valid_indices):
            if idx < len(metadata):
                # Convert metadata to SearchResult format
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

        logger.info(f"Found {len(results)} relevant chunks for query.")
        logger.debug(f"Returning {len(results)} results to client")
        return QueryResponse(results=results)

    except Exception as e:
        logger.error(f"Error during query processing: {e}", exc_info=True)
        logger.debug(f"Query that failed: '{query_text}'")
        logger.debug(f"Index status at failure: {'Available' if index else 'None'}")
        logger.debug(f"Metadata status at failure: {len(metadata) if metadata else 0}")
        raise HTTPException(status_code=500, detail="An error occurred during search.")
