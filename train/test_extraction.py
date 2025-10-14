#!/usr/bin/env python3
"""
Quick test script to extract text from just a few documents.
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from extract_text_from_documents import DocumentTextExtractor


def main():
    """Test extraction with detailed logging."""
    # Paths
    document_raw_path = (
        "/Users/bradencurtis/MYWORKSPACE/ScanPro/test_data/es/document_raw"
    )
    document_dataset_path = (
        "/Users/bradencurtis/MYWORKSPACE/ScanPro/test_data/es/document_dataset"
    )

    # Create extractor
    extractor = DocumentTextExtractor(document_raw_path, document_dataset_path)

    # Extract all texts
    success = extractor.extract_all_texts()

    if success:
        print("✅ Test extraction completed successfully!")
        print(f"📁 Texts saved to: {document_dataset_path}")
    else:
        print("❌ Test extraction failed!")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
