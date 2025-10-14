#!/usr/bin/env python3
"""
Helper functions for incremental model updates based on user feedback.
These functions update existing model embeddings without retraining from scratch.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import config
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


def load_existing_embeddings(model_path: str) -> Dict[str, List[float]]:
    """Load existing category embeddings from the model directory."""
    try:
        embeddings_file = Path(model_path) / "category_embeddings.json"
        if not embeddings_file.exists():
            logger.warning("No embeddings file found")
            return {}

        with open(embeddings_file, "r", encoding="utf-8") as f:
            embeddings_data = json.load(f)

        logger.info(f"Loaded embeddings for {len(embeddings_data)} categories")
        return embeddings_data

    except Exception as e:
        logger.error(f"Error loading existing embeddings: {e}")
        return {}


def extract_corrected_documents(
    corrections: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Extract text content from corrected documents organized by category."""
    corrected_docs = {}

    for correction in corrections:
        filename = correction["filename"]
        category = correction["to_category"]

        # Get document path from category metadata
        doc_path = _get_document_path(filename, category)
        if not doc_path or not doc_path.exists():
            logger.warning(f"Document not found: {filename}")
            continue

        # Extract text content
        text_content = _extract_text_from_document(doc_path)
        if text_content:
            if category not in corrected_docs:
                corrected_docs[category] = []
            corrected_docs[category].append(text_content)
            logger.debug(f"Extracted text for {filename} in category {category}")

    logger.info(
        f"Extracted corrected documents: {sum(len(docs) for docs in corrected_docs.values())} total"
    )
    return corrected_docs


def _get_document_path(filename: str, category: str) -> Path:
    """Get the file path for a document from category metadata."""
    try:
        # Load category metadata to find document path
        category_metadata_file = config.APP_DIR / "category_metadata.json"
        if not category_metadata_file.exists():
            return None

        with open(category_metadata_file, "r", encoding="utf-8") as f:
            category_metadata = json.load(f)

        if category in category_metadata and filename in category_metadata[category]:
            file_path = category_metadata[category][filename].get("file_path")
            if file_path:
                return Path(file_path)

        return None

    except Exception as e:
        logger.error(f"Error getting document path for {filename}: {e}")
        return None


def _extract_text_from_document(doc_path: Path) -> str:
    """Extract text content from a document file."""
    try:
        if doc_path.suffix.lower() == ".txt":
            with open(doc_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            # For other file types, we'd need OCR processing
            # For now, return empty string - this would need to be implemented
            logger.warning(f"Text extraction not implemented for {doc_path.suffix}")
            return ""

    except Exception as e:
        logger.error(f"Error extracting text from {doc_path}: {e}")
        return ""


def generate_embeddings_for_documents(
    corrected_docs: Dict[str, List[str]], model: SentenceTransformer
) -> Dict[str, np.ndarray]:
    """Generate embeddings for corrected documents."""
    if not model:
        logger.error("Model not initialized")
        return {}

    new_embeddings = {}

    for category, texts in corrected_docs.items():
        if not texts:
            continue

        try:
            # Generate embeddings for all texts in this category
            embeddings = model.encode(texts)

            # Calculate average embedding for this category
            category_embedding = np.mean(embeddings, axis=0)
            new_embeddings[category] = category_embedding

            logger.info(
                f"Generated embeddings for {len(texts)} documents in {category}"
            )

        except Exception as e:
            logger.error(f"Error generating embeddings for {category}: {e}")
            continue

    return new_embeddings


def recalculate_category_embeddings(
    existing_embeddings: Dict[str, List[float]],
    new_embeddings: Dict[str, np.ndarray],
    corrected_docs: Dict[str, List[str]],
) -> Dict[str, List[float]]:
    """Recalculate category embeddings by combining existing and new data."""
    updated_embeddings = existing_embeddings.copy()

    for category, new_embedding in new_embeddings.items():
        if category in updated_embeddings:
            # Convert existing embedding to numpy array
            existing_embedding = np.array(updated_embeddings[category])

            # Calculate weighted average (existing weight = 0.7, new weight = 0.3)
            # This gives more weight to existing data while incorporating new corrections
            weight_existing = 0.7
            weight_new = 0.3

            updated_embedding = (
                weight_existing * existing_embedding + weight_new * new_embedding
            )

            updated_embeddings[category] = updated_embedding.tolist()
            logger.info(f"Updated embeddings for category: {category}")
        else:
            # New category - use new embedding directly
            updated_embeddings[category] = new_embedding.tolist()
            logger.info(f"Added new category: {category}")

    return updated_embeddings


def save_updated_embeddings(
    updated_embeddings: Dict[str, List[float]], model_path: str
) -> bool:
    """Save updated embeddings to the model directory."""
    try:
        if not model_path:
            logger.error("No model path available")
            return False

        # Create backup of existing embeddings
        embeddings_file = Path(model_path) / "category_embeddings.json"
        backup_file = Path(model_path) / "category_embeddings.json.backup"

        if embeddings_file.exists():
            embeddings_file.rename(backup_file)
            logger.info("Created backup of existing embeddings")

        # Save updated embeddings
        with open(embeddings_file, "w", encoding="utf-8") as f:
            json.dump(updated_embeddings, f, indent=2)

        logger.info(f"Saved updated embeddings to {embeddings_file}")
        return True

    except Exception as e:
        logger.error(f"Error saving updated embeddings: {e}")
        return False


def update_model_embeddings_incremental(
    corrections: List[Dict[str, Any]], model_path: str
) -> bool:
    """Complete incremental model update pipeline."""
    try:
        logger.info("Starting incremental model update...")

        # Initialize model
        model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Initialized model for updates")

        # Load existing embeddings
        existing_embeddings = load_existing_embeddings(model_path)
        if not existing_embeddings:
            logger.error("No existing embeddings found")
            return False

        # Extract corrected documents
        corrected_docs = extract_corrected_documents(corrections)
        if not corrected_docs:
            logger.warning("No corrected documents found")
            return True  # Not an error, just nothing to update

        # Generate embeddings for corrected documents
        new_embeddings = generate_embeddings_for_documents(corrected_docs, model)
        if not new_embeddings:
            logger.warning("No new embeddings generated")
            return True

        # Recalculate category embeddings
        updated_embeddings = recalculate_category_embeddings(
            existing_embeddings, new_embeddings, corrected_docs
        )

        # Save updated embeddings
        if save_updated_embeddings(updated_embeddings, model_path):
            logger.info("Model embeddings updated successfully")
            return True
        else:
            logger.error("Failed to save updated embeddings")
            return False

    except Exception as e:
        logger.error(f"Error in incremental model update: {e}")
        return False
