"""
FAISS embeddings index for document search and retrieval.
Uses IndexFlatL2 (exact L2 distance search) - no training required.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@dataclass
class EmbeddingMetadata:
    """Metadata associated with an embedding."""
    document_id: str
    page_number: int
    text: str

import faiss

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
        self.original_sentences: List[str] = []  # Kept for backward compatibility
        self.metadata: List[EmbeddingMetadata] = []  # Stores document_id, page_number, and text
        self._is_trained = True  # Flat index doesn't need training

        # Create Flat index structure (no training required, can add immediately)
        self.embeddings = faiss.IndexFlatL2(dimension)

        # Load existing index if path is provided
        if index_path and index_path.exists():
            try:
                self.load_embeddings(index_path)
                logger.info(f"Loaded FAISS index from {index_path} with {len(self.original_sentences)} embeddings")
            except Exception as e:
                logger.warning(f"Failed to load existing index from {index_path}: {e}")
                logger.info("Creating new index")
        else:
            logger.info("Initializing new FAISS index")

    def add(
        self, 
        sentences: List[str],
        document_id: Optional[str] = None,
        page_numbers: Optional[List[int]] = None,
    ) -> None:
        """
        Add sentences to the index with optional metadata.

        Args:
            sentences: List of sentences/text to add to the index
            document_id: Document ID (file hash) - if provided, applies to all sentences
            page_numbers: List of page numbers corresponding to each sentence.
                         If None and document_id is provided, defaults to sequential pages (0, 1, 2...)
        """
        if not sentences:
            return

        # Handle metadata
        if document_id is not None:
            # If page_numbers not provided, default to sequential starting from 0
            if page_numbers is None:
                page_numbers = list(range(len(sentences)))
            elif len(page_numbers) != len(sentences):
                logger.warning(
                    f"Page numbers count ({len(page_numbers)}) doesn't match sentences count ({len(sentences)}). "
                    "Using sequential page numbers."
                )
                page_numbers = list(range(len(sentences)))
            
            # Create metadata for each sentence
            for i, sentence in enumerate(sentences):
                metadata = EmbeddingMetadata(
                    document_id=document_id,
                    page_number=page_numbers[i] if i < len(page_numbers) else i,
                    text=sentence
                )
                self.metadata.append(metadata)
                self.original_sentences.append(sentence)  # Keep for backward compatibility
        else:
            # No metadata provided - just add sentences (backward compatible)
            self.original_sentences.extend(sentences)
            # Create metadata with None values for backward compatibility
            for sentence in sentences:
                self.metadata.append(EmbeddingMetadata(
                    document_id="",
                    page_number=-1,
                    text=sentence
                ))

        # Generate embeddings
        try:
            new_embeddings = self.transformer.encode(sentences, convert_to_tensor=False)
            
            # Ensure embeddings are in float32 format for FAISS
            new_embeddings = new_embeddings.astype(np.float32)
            
            # Add embeddings directly (Flat index doesn't require training)
            self.embeddings.add(new_embeddings)
            logger.debug(f"Added {len(sentences)} sentences to FAISS index")

        except Exception as e:
            logger.error(f"Failed to add embeddings to index: {e}")
            raise

    def remove(self, indexes: List[int]) -> None:
        """
        Remove embeddings from the index by their indexes.

        Args:
            indexes: List of indexes to remove
        """
        if not indexes:
            return

        try:
            # Remove from FAISS index
            index_array = np.array(indexes, dtype=np.int64)
            self.embeddings.remove_ids(index_array)

            # Remove from original sentences and metadata lists
            # Sort in reverse order to avoid index shifting issues
            for idx in sorted(indexes, reverse=True):
                if 0 <= idx < len(self.original_sentences):
                    del self.original_sentences[idx]
                if 0 <= idx < len(self.metadata):
                    del self.metadata[idx]

            logger.info(f"Removed {len(indexes)} embeddings from index")

        except Exception as e:
            logger.error(f"Failed to remove embeddings from index: {e}")
            raise

    def search(self, sentence: str, depth: int = 10) -> List[str]:
        """
        Search for similar sentences in the index (backward compatible method).

        Args:
            sentence: Query sentence to search for
            depth: Number of top results to return

        Returns:
            List of top matching sentences
        """
        results = self.search_with_metadata(sentence, depth)
        return [metadata.text for metadata in results]

    def search_with_metadata(
        self, sentence: str, depth: int = 10
    ) -> List[EmbeddingMetadata]:
        """
        Search for similar sentences in the index and return metadata.

        Args:
            sentence: Query sentence to search for
            depth: Number of top results to return

        Returns:
            List of EmbeddingMetadata objects containing document_id, page_number, and text
        """
        results, _ = self.search_with_metadata_and_distances(sentence, depth)
        return results

    def search_with_metadata_and_distances(
        self, sentence: str, depth: int = 10
    ) -> Tuple[List[EmbeddingMetadata], List[float]]:
        """
        Search for similar sentences in the index and return metadata with distances.

        Args:
            sentence: Query sentence to search for
            depth: Number of top results to return

        Returns:
            Tuple of (List[EmbeddingMetadata], List[float]) containing metadata and distances
        """
        if self.embeddings.ntotal == 0:
            logger.warning("Index is empty, returning empty results")
            return [], []

        try:
            # Generate embedding for query sentence
            embedded_sentence = self.transformer.encode([sentence], convert_to_tensor=False)
            embedded_sentence = embedded_sentence.astype(np.float32)

            # Search in FAISS index
            distances, indices = self.embeddings.search(embedded_sentence, depth)

            # Get metadata from indices
            results = []
            result_distances = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.metadata):
                    results.append(self.metadata[idx.item()])
                    result_distances.append(float(distances[0][i]))

            logger.debug(f"Found {len(results)} results for query: {sentence[:50]}...")
            return results, result_distances

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], []

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
        Save the FAISS index and metadata to disk.

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

            # Save FAISS index
            faiss.write_index(self.embeddings, str(save_path))
            logger.info(f"Saved FAISS index to {save_path}")

            # Save metadata as JSON (same directory, .json extension)
            metadata_path = save_path.with_suffix('.json')
            metadata_dict = [
                {
                    "document_id": meta.document_id,
                    "page_number": meta.page_number,
                    "text": meta.text
                }
                for meta in self.metadata
            ]
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved metadata to {metadata_path}")

        except Exception as e:
            logger.error(f"Failed to save embeddings to {save_path}: {e}")
            raise

    def load_embeddings(self, path: Optional[Path] = None) -> None:
        """
        Load the FAISS index and metadata from disk.

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

            # Load metadata from JSON file
            metadata_path = load_path.with_suffix('.json')
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata_list = json.load(f)
                
                # Reconstruct metadata objects
                self.metadata = [
                    EmbeddingMetadata(
                        document_id=meta["document_id"],
                        page_number=meta["page_number"],
                        text=meta["text"]
                    )
                    for meta in metadata_list
                ]
                
                # Reconstruct original_sentences for backward compatibility
                self.original_sentences = [meta.text for meta in self.metadata]
                
                logger.info(f"Loaded {len(self.metadata)} metadata entries from {metadata_path}")
            else:
                logger.warning(f"Metadata file not found at {metadata_path}. Metadata will be empty.")
                self.metadata = []
                self.original_sentences = []

        except Exception as e:
            logger.error(f"Failed to load embeddings from {load_path}: {e}")
            raise

    def get_stats(self) -> dict:
        """
        Get statistics about the index.

        Returns:
            Dictionary with index statistics
        """
        # Count unique documents in metadata
        unique_documents = set(
            meta.document_id for meta in self.metadata if meta.document_id
        ) if self.metadata else set()
        
        return {
            "total_embeddings": self.embeddings.ntotal,
            "original_sentences_count": len(self.original_sentences),
            "metadata_count": len(self.metadata),
            "unique_documents": len(unique_documents),
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
