#!/usr/bin/env python3
"""
Migration script to convert category_metadata.json from array-based to filename-based structure.

This script will:
1. Read the current array-based structure
2. Convert each category to filename: object mapping
3. Save the new structure
4. Create a backup of the original file
"""

import json
import logging
import shutil
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_category_metadata():
    """Migrate category metadata from array-based to filename-based structure."""
    metadata_file = config.APP_DIR / "category_metadata.json"

    if not metadata_file.exists():
        logger.info("No category_metadata.json file found")
        return

    # Create backup
    backup_file = metadata_file.with_suffix(".json.backup")
    shutil.copy2(metadata_file, backup_file)
    logger.info(f"Created backup: {backup_file}")

    # Read current structure
    with open(metadata_file, "r", encoding="utf-8") as f:
        old_metadata = json.load(f)

    # Convert to new structure
    new_metadata = {}

    for category, documents in old_metadata.items():
        if isinstance(documents, list):
            # Convert array to filename: object mapping
            new_metadata[category] = {}
            for doc in documents:
                if isinstance(doc, dict) and "filename" in doc:
                    filename = doc["filename"]
                    # Remove filename from the object since it's now the key
                    doc_copy = doc.copy()
                    doc_copy.pop("filename", None)
                    new_metadata[category][filename] = doc_copy
                else:
                    logger.warning(f"Skipping invalid document in {category}: {doc}")
        else:
            # Keep non-array values as-is
            new_metadata[category] = documents

    # Save new structure
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(new_metadata, f, indent=2)

    logger.info("Migration completed successfully")

    # Log statistics
    total_docs = sum(
        len(docs) for docs in new_metadata.values() if isinstance(docs, dict)
    )
    logger.info(
        f"Migrated {total_docs} documents across {len(new_metadata)} categories"
    )


def verify_migration():
    """Verify the migration was successful."""
    metadata_file = config.APP_DIR / "category_metadata.json"

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Check structure
    for category, documents in metadata.items():
        if isinstance(documents, dict):
            logger.info(f"✓ {category}: {len(documents)} documents (filename-based)")
            # Verify each document has required fields
            for filename, doc in documents.items():
                if not isinstance(doc, dict):
                    logger.error(f"✗ {category}[{filename}]: Not a dict")
                elif "category" not in doc:
                    logger.error(f"✗ {category}[{filename}]: Missing 'category' field")
        else:
            logger.info(f"✓ {category}: {documents} (non-document data)")


if __name__ == "__main__":
    migrate_category_metadata()
    verify_migration()
