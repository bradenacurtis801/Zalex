#!/usr/bin/env python3
"""
Migration script to convert existing files to content-based filenames.

This script will:
1. Scan the upload directory for files without content-based names
2. Calculate SHA-256 hashes for each file
3. Rename files to content-based format
4. Update any references in metadata files
"""

import json
import logging
import os
import shutil
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import config
from src.utils.file_hasher import calculate_file_hash, get_content_based_filename

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_content_based_filename(filename: str) -> bool:
    """
    Check if a filename is already content-based.

    Args:
        filename: Filename to check

    Returns:
        True if content-based, False otherwise
    """
    # Content-based filenames start with 64-character hash followed by underscore
    return (
        len(filename) > 64
        and filename[64] == "_"
        and all(c in "0123456789abcdef" for c in filename[:64])
    )


def migrate_files():
    """Migrate files to content-based filenames."""
    upload_dir = Path(config.UPLOAD_DIR)

    if not upload_dir.exists():
        logger.info(f"Upload directory {upload_dir} does not exist")
        return

    # Find files that need migration
    files_to_migrate = []
    for file_path in upload_dir.iterdir():
        if file_path.is_file() and not is_content_based_filename(file_path.name):
            files_to_migrate.append(file_path)

    if not files_to_migrate:
        logger.info("No files need migration")
        return

    logger.info(f"Found {len(files_to_migrate)} files to migrate")

    # Track filename changes for metadata updates
    filename_changes = {}

    for file_path in files_to_migrate:
        try:
            logger.info(f"Processing {file_path.name}...")

            # Calculate hash
            file_hash = calculate_file_hash(str(file_path))
            if not file_hash:
                logger.error(f"Failed to calculate hash for {file_path.name}")
                continue

            # Generate new filename
            new_filename = get_content_based_filename(file_path.name, file_hash)
            new_file_path = upload_dir / new_filename

            # Check if file with same content already exists
            if new_file_path.exists():
                logger.info(f"File with same content already exists: {new_filename}")
                # Remove duplicate
                file_path.unlink()
                filename_changes[file_path.name] = new_filename
                continue

            # Rename file
            file_path.rename(new_file_path)
            filename_changes[file_path.name] = new_filename
            logger.info(f"Renamed {file_path.name} to {new_filename}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")

    # Update metadata files if they exist
    update_metadata_files(filename_changes)

    logger.info(f"Migration completed. {len(filename_changes)} files processed.")


def update_metadata_files(filename_changes: dict):
    """
    Update metadata files with new filenames.

    Args:
        filename_changes: Dictionary mapping old filenames to new filenames
    """
    if not filename_changes:
        return

    # Update document metadata
    metadata_file = config.APP_DIR / "document_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            updated = False
            for doc in metadata:
                if doc.get("filename") in filename_changes:
                    old_filename = doc["filename"]
                    new_filename = filename_changes[old_filename]
                    doc["filename"] = new_filename
                    updated = True
                    logger.info(f"Updated metadata: {old_filename} -> {new_filename}")

            if updated:
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
                logger.info("Updated document metadata file")

        except Exception as e:
            logger.error(f"Error updating metadata file: {e}")

    # Update category metadata
    category_metadata_file = config.APP_DIR / "category_metadata.json"
    if category_metadata_file.exists():
        try:
            with open(category_metadata_file, "r", encoding="utf-8") as f:
                category_metadata = json.load(f)

            updated = False
            for category, docs in category_metadata.items():
                for doc in docs:
                    if doc.get("filename") in filename_changes:
                        old_filename = doc["filename"]
                        new_filename = filename_changes[old_filename]
                        doc["filename"] = new_filename
                        updated = True
                        logger.info(
                            f"Updated category metadata: {old_filename} -> {new_filename}"
                        )

            if updated:
                with open(category_metadata_file, "w", encoding="utf-8") as f:
                    json.dump(category_metadata, f, indent=2)
                logger.info("Updated category metadata file")

        except Exception as e:
            logger.error(f"Error updating category metadata file: {e}")


if __name__ == "__main__":
    migrate_files()
