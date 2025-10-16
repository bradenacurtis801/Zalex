"""File hashing utilities for content-based identification."""

import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
    """
    Calculate the hash of a file's contents.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string or None if error
    """
    try:
        hash_obj = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return None


def get_content_based_filename(original_filename: str, file_hash: str) -> str:
    """
    Generate a content-based filename using the file hash.

    Args:
        original_filename: Original filename with extension
        file_hash: Content hash of the file

    Returns:
        New filename in format: {original_name}_{hash}
    """
    # Extract extension from original filename
    path = Path(original_filename)
    extension = path.suffix
    name_without_ext = path.stem

    # Create new filename: {original_name}_{hash}.{ext}
    return f"{name_without_ext}_{file_hash}{extension}"


def extract_hash_from_filename(filename: str) -> Optional[str]:
    """
    Extract the hash from a content-based filename.

    Args:
        filename: Content-based filename

    Returns:
        Hash string or None if not found
    """
    try:
        # Format: {original_name}_{hash}.{ext}
        # Hash is typically 64 characters for SHA-256
        # Find the last underscore before the extension
        path = Path(filename)
        name_without_ext = path.stem
        
        # Look for a 64-character hash at the end of the filename
        if len(name_without_ext) > 64 and name_without_ext[-64:].replace('_', '').isalnum():
            # Check if the last 64 characters look like a hash (hex characters)
            potential_hash = name_without_ext[-64:]
            if all(c in '0123456789abcdef' for c in potential_hash):
                return potential_hash
        return None
    except Exception:
        return None
