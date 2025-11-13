"""
FAISS embeddings index for document search and retrieval.
Uses IndexFlatL2 (exact L2 distance search) - no training required.

Note: This class only handles embeddings. Metadata is stored separately in the database.
"""

import logging
import numpy as np
from pathlib import Path
import faiss
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)

# Singleton instance
_embeddings_index: Optional["EmbeddingsIndex"] = None


class EmbeddingsIndex:
    """
    FAISS embeddings index wrapper for efficient document search.
    Uses IndexFlatL2 (exact L2 distance search) - no training required.
    """

    def __init__(
        self,
        transformer: "SentenceTransformer",
        index_path: Optional[Path] = None,
        dimension: Optional[int] = None,
    ):
        """
        Initialize the embeddings index.

        Args:
            transformer: SentenceTransformer model for encoding text
            index_path: Optional path to load/save the index file
            dimension: Embedding dimension (auto-detected from transformer if None)
        """
        self.transformer = transformer
        self.index_path = index_path
        
        # Auto-detect dimension from transformer if not provided
        if dimension is None:
            try:
                dimension = transformer.get_sentence_embedding_dimension()
            except AttributeError:
                # Fallback for models that don't have this method
                dimension = 384  # Default for all-MiniLM-L6-v2
                logger.warning("Could not auto-detect dimension, using default 384")
        
        self.dimension = dimension
        self._is_trained = True  # Flat index doesn't need training

        # Create Flat index structure (no training required, can add immediately)
        self.embeddings = faiss.IndexFlatL2(dimension)

        # Load existing index if path is provided
        if index_path and index_path.exists():
            try:
                self.load_embeddings(index_path)
                logger.info(f"Loaded FAISS index from {index_path} with {self.embeddings.ntotal} embeddings")
            except Exception as e:
                logger.warning(f"Failed to load existing index from {index_path}: {e}")
                logger.info("Creating new index")
        else:
            logger.info("Initializing new FAISS index")

    def add(self, sentences: List[str]) -> List[int]:
        """
        Add sentences to the FAISS index (embeddings only) and save automatically.
        Metadata should be stored separately in the database.

        Args:
            sentences: List of sentences/text to add to the index

        Returns:
            List of FAISS index positions for the added embeddings
        """
        if not sentences:
            return []

        # Generate embeddings
        try:
            # Get the starting index position before adding
            start_index = self.embeddings.ntotal
            
            new_embeddings = self.transformer.encode(sentences, convert_to_tensor=False)
            
            # Ensure embeddings are in float32 format for FAISS
            new_embeddings = new_embeddings.astype(np.float32)
            
            # Add embeddings directly to FAISS (Flat index doesn't require training)
            self.embeddings.add(new_embeddings)
            
            # Return the index positions of the added embeddings
            indices = list(range(start_index, self.embeddings.ntotal))
            logger.debug(f"Added {len(sentences)} embeddings to FAISS index at positions {indices}")
            
            # Automatically save the index
            self.store_embeddings()
            
            return indices

        except Exception as e:
            logger.error(f"Failed to add embeddings to FAISS index: {e}")
            raise

    def remove(self, indexes: List[int]) -> None:
        """
        Remove embeddings from the index by their indexes.
        Note: Metadata removal should be handled separately in the database.

        Args:
            indexes: List of indexes to remove
        """
        if not indexes:
            return

        try:
            # Remove from FAISS index
            index_array = np.array(indexes, dtype=np.int64)
            self.embeddings.remove_ids(index_array)

            logger.info(f"Removed {len(indexes)} embeddings from index")
            logger.warning("Note: Metadata in database should be removed separately")

        except Exception as e:
            logger.error(f"Failed to remove embeddings from index: {e}")
            raise

    def search_indices(self, sentence: str, depth: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for similar embeddings in the index and return FAISS indices and distances.
        Metadata should be retrieved separately from the database using the returned indices.

        Args:
            sentence: Query sentence to search for
            depth: Number of top results to return

        Returns:
            Tuple of (distances, indices) from FAISS search
        """
        if self.embeddings.ntotal == 0:
            logger.warning("Index is empty, returning empty results")
            return np.array([]), np.array([])

        try:
            # Generate embedding for query sentence
            embedded_sentence = self.transformer.encode([sentence], convert_to_tensor=False)
            embedded_sentence = embedded_sentence.astype(np.float32)

            # Search in FAISS index
            distances, indices = self.embeddings.search(embedded_sentence, depth)

            logger.debug(f"Found {len(indices[0])} results for query: {sentence[:50]}...")
            return distances[0], indices[0]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return np.array([]), np.array([])

    def train(self, sentences: Optional[List[str]] = None) -> None:
        """
        Train the FAISS index structure.
        
        Note: Flat indexes (IndexFlatL2) don't require training.
        This method is kept for backward compatibility but is a no-op.

        Args:
            sentences: Optional sentences to train on (ignored for flat index).
        """
        logger.debug("Flat index (IndexFlatL2) doesn't require training - skipping")
        # Flat index is always ready to use, no training needed

    def store_embeddings(self, path: Optional[Path] = None) -> None:
        """
        Save the FAISS index to disk.
        Note: Metadata is stored separately in the database.

        Args:
            path: Optional path to save to. Uses self.index_path if not provided.
        """
        save_path = path or self.index_path
        if not save_path:
            logger.warning("No path provided for saving embeddings")
            return

        try:
            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # Save FAISS index only
            faiss.write_index(self.embeddings, str(save_path))
            logger.info(f"Saved FAISS index to {save_path}")

        except Exception as e:
            logger.error(f"Failed to save embeddings to {save_path}: {e}")
            raise

    def load_embeddings(self, path: Optional[Path] = None) -> None:
        """
        Load the FAISS index from disk.
        Note: Metadata is loaded separately from the database.

        Args:
            path: Optional path to load from. Uses self.index_path if not provided.
        """
        load_path = path or self.index_path
        if not load_path or not load_path.exists():
            logger.warning(f"Index file not found at {load_path}")
            return

        try:
            # Load FAISS index
            loaded_index = faiss.read_index(str(load_path))
            
            # Check if loaded index is the correct type (IndexFlatL2)
            index_type = type(loaded_index).__name__
            
            if "IndexIVFPQ" in index_type or "IndexIVF" in index_type:
                error_msg = (
                    f"FAISS index file at {load_path} is of incorrect type: {index_type}. "
                    f"Expected IndexFlatL2. "
                    f"Please delete the old index file and let the system recreate it, "
                    f"or migrate the index manually."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Correct type, use it
            self.embeddings = loaded_index
            self._is_trained = True
            logger.info(f"Loaded FAISS index from {load_path} (type: {index_type})")
            logger.info("Note: Metadata should be loaded separately from the database")

        except Exception as e:
            logger.error(f"Failed to load embeddings from {load_path}: {e}")
            raise

    def get_stats(self) -> dict:
        """
        Get statistics about the FAISS index.
        Note: Metadata statistics should be queried separately from the database.

        Returns:
            Dictionary with index statistics
        """
        return {
            "total_embeddings": self.embeddings.ntotal,
            "is_trained": self._is_trained,
            "dimension": self.dimension,
            "index_path": str(self.index_path) if self.index_path else None,
        }


def get_embeddings_index(
    transformer: "SentenceTransformer",
    index_path: Optional[Path] = None,
    force_reload: bool = False,
) -> EmbeddingsIndex:
    """
    Get or create the singleton embeddings index instance.

    Args:
        transformer: SentenceTransformer model for encoding
        index_path: Path to the index file
        force_reload: If True, recreate the index even if it exists

    Returns:
        EmbeddingsIndex: The singleton embeddings index instance
    """
    global _embeddings_index

    if _embeddings_index is None or force_reload:
        _embeddings_index = EmbeddingsIndex(transformer, index_path)
    elif index_path and _embeddings_index.index_path != index_path:
        # Update path if different
        _embeddings_index.index_path = index_path

    return _embeddings_index
