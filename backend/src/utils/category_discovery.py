"""Utility functions for discovering document categories from directory structure."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


def discover_categories_from_directory(base_path: str) -> List[str]:
    """
    Discover document categories by scanning the directory structure.

    Looks for subdirectories in the document_raw folder and uses their names as categories.

    Args:
        base_path: Path to the document_raw directory

    Returns:
        List of category names found in the directory structure
    """
    logger.info(f"Discovering categories from directory: {base_path}")

    if not os.path.exists(base_path):
        logger.warning(f"Directory does not exist: {base_path}")
        return []

    categories = []

    try:
        # Get all subdirectories in the base path
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                # Check if the directory contains files (not empty)
                if any(
                    os.path.isfile(os.path.join(item_path, f))
                    for f in os.listdir(item_path)
                ):
                    categories.append(item)
                    logger.info(f"Found category: {item}")
                else:
                    logger.debug(f"Skipping empty directory: {item}")

        categories.sort()  # Sort for consistent ordering
        logger.info(f"Discovered {len(categories)} categories: {categories}")

    except Exception as e:
        logger.error(f"Error discovering categories: {e}")
        return []

    return categories


def discover_categories_from_multiple_paths(paths: List[str]) -> List[str]:
    """
    Discover categories from multiple directory paths and merge them.

    Args:
        paths: List of paths to scan for categories

    Returns:
        Sorted list of unique category names
    """
    all_categories = set()

    for path in paths:
        categories = discover_categories_from_directory(path)
        all_categories.update(categories)

    return sorted(list(all_categories))


def get_category_file_count(base_path: str, category: str) -> int:
    """
    Get the number of files in a specific category directory.

    Args:
        base_path: Path to the document_raw directory
        category: Category name

    Returns:
        Number of files in the category directory
    """
    category_path = os.path.join(base_path, category)

    if not os.path.exists(category_path):
        return 0

    try:
        files = [
            f
            for f in os.listdir(category_path)
            if os.path.isfile(os.path.join(category_path, f))
        ]
        return len(files)
    except Exception as e:
        logger.error(f"Error counting files in category {category}: {e}")
        return 0


def get_category_summary(base_path: str) -> Dict[str, int]:
    """
    Get a summary of all categories and their file counts.

    Args:
        base_path: Path to the document_raw directory

    Returns:
        Dictionary mapping category names to file counts
    """
    categories = discover_categories_from_directory(base_path)
    summary = {}

    for category in categories:
        file_count = get_category_file_count(base_path, category)
        summary[category] = file_count

    return summary


def ensure_category_directories_exist(base_path: str, categories: List[str]) -> None:
    """
    Ensure that all category directories exist in the document_dataset path.

    Args:
        base_path: Path to the document_dataset directory
        categories: List of category names to create directories for
    """
    for category in categories:
        category_path = os.path.join(base_path, category)
        os.makedirs(category_path, exist_ok=True)
        logger.debug(f"Ensured directory exists: {category_path}")


def get_document_dataset_path(document_raw_path: str) -> str:
    """
    Convert a document_raw path to the corresponding document_dataset path.

    Args:
        document_raw_path: Path to document_raw directory

    Returns:
        Path to the corresponding document_dataset directory
    """
    # Replace 'document_raw' with 'document_dataset' in the path
    return document_raw_path.replace("document_raw", "document_dataset")
