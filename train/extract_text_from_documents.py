#!/usr/bin/env python3
"""
Text extraction script for processing documents from document_raw to document_dataset.

This script:
1. Scans the document_raw directory structure to discover categories
2. Processes all images and PDFs in each category
3. Extracts text using OCR (Tesseract)
4. Saves the extracted text to document_dataset with the same structure
"""

import logging
import os
import sys
from pathlib import Path
from typing import List

# Add the backend directory to the Python path so we can import the OCR modules
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import fitz  # PyMuPDF for PDF processing
from PIL import Image
from src.ocr.base import OCREngine
from src.ocr.factory import get_default_ocr_engine

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentTextExtractor:
    """Extracts text from documents and organizes them by category."""

    def __init__(
        self,
        document_raw_path: str,
        document_dataset_path: str,
    ):
        """
        Initialize the text extractor.

        Args:
            document_raw_path: Path to the document_raw directory
            document_dataset_path: Path to the document_dataset directory
        """
        self.document_raw_path = Path(document_raw_path)
        self.document_dataset_path = Path(document_dataset_path)
        self.ocr_engine: OCREngine = None

    def initialize_ocr(self) -> bool:
        """Initialize the OCR engine."""
        try:
            self.ocr_engine = get_default_ocr_engine()
            self.ocr_engine.initialize()
            logger.info("OCR engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {e}")
            return False

    def discover_categories(self) -> List[str]:
        """Discover categories from the document_raw directory structure."""
        categories = []

        if not self.document_raw_path.exists():
            logger.error(f"Document raw path does not exist: {self.document_raw_path}")
            return categories

        for item in self.document_raw_path.iterdir():
            if item.is_dir():
                # Check if the directory contains files
                if any(f.is_file() for f in item.iterdir()):
                    categories.append(item.name)
                    logger.info(f"Found category: {item.name}")
                else:
                    logger.debug(f"Skipping empty directory: {item.name}")

        categories.sort()
        logger.info(f"Discovered {len(categories)} categories: {categories}")
        return categories

    def process_image(self, image_path: Path) -> str:
        """
        Process an image file and extract text using OCR.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text
        """
        try:
            logger.info(f"🖼️  Processing image: {image_path.name}")
            logger.info(f"   📁 Full path: {image_path}")
            logger.info(f"   📏 File size: {image_path.stat().st_size} bytes")

            logger.info(f"   🔍 Starting OCR extraction...")
            text = self.ocr_engine.extract_text(str(image_path))
            logger.info(f"   ✅ OCR completed, extracted {len(text)} characters")

            return text.strip()
        except Exception as e:
            logger.error(f"❌ Failed to process image {image_path}: {e}")
            return ""

    def process_pdf(self, pdf_path: Path) -> str:
        """
        Process a PDF file and extract text using OCR on each page.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Combined extracted text from all pages
        """
        try:
            logger.info(f"📄 Processing PDF: {pdf_path.name}")
            logger.info(f"   📁 Full path: {pdf_path}")
            logger.info(f"   📏 File size: {pdf_path.stat().st_size} bytes")

            logger.info(f"   📖 Opening PDF...")
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)
            logger.info(f"   📊 PDF has {total_pages} pages")

            all_text = []

            for page_num in range(total_pages):
                logger.info(f"   📄 Processing page {page_num + 1}/{total_pages}")

                page = doc[page_num]
                logger.info(f"      🔄 Converting page to image...")
                # Convert PDF page to image
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                logger.info(f"      📏 Image size: {len(img_bytes)} bytes")

                logger.info(f"      🔍 Starting OCR on page...")
                # Extract text from the image bytes
                text = self.ocr_engine.extract_text_from_bytes(img_bytes, "png")
                if text.strip():
                    all_text.append(text.strip())
                    logger.info(
                        f"      ✅ Page {page_num + 1}: extracted {len(text)} characters"
                    )
                else:
                    logger.warning(f"      ⚠️  Page {page_num + 1}: no text extracted")

            logger.info(f"   📖 Closing PDF...")
            doc.close()

            combined_text = "\n".join(all_text)
            logger.info(
                f"   ✅ PDF processing complete: {len(combined_text)} total characters"
            )
            return combined_text

        except Exception as e:
            logger.error(f"❌ Failed to process PDF {pdf_path}: {e}")
            return ""

    def process_document(self, file_path: Path) -> str:
        """
        Process a single document (image or PDF) and extract text.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text
        """
        file_extension = file_path.suffix.lower()
        logger.info(f"🔍 Determining file type: {file_extension}")

        if file_extension in [".jpg", ".jpeg", ".png", ".webp"]:
            logger.info(f"   → Processing as IMAGE")
            return self.process_image(file_path)
        elif file_extension == ".pdf":
            logger.info(f"   → Processing as PDF")
            return self.process_pdf(file_path)
        else:
            logger.warning(f"❌ Unsupported file type: {file_path}")
            return ""

    def extract_text_for_category(self, category: str) -> int:
        """
        Extract text from all documents in a category and save immediately.

        Args:
            category: Category name

        Returns:
            Number of files successfully processed
        """
        category_dir = self.document_raw_path / category
        success_count = 0

        if not category_dir.exists():
            logger.warning(f"Category directory does not exist: {category_dir}")
            return success_count

        # Get all files in the category directory
        files = [f for f in category_dir.iterdir() if f.is_file()]
        logger.info(f"📁 Found {len(files)} files in category '{category}'")

        # Ensure the output directory exists
        output_category_dir = self.document_dataset_path / category
        output_category_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"   📁 Output directory: {output_category_dir}")

        for i, file_path in enumerate(files, 1):
            logger.info(f"")
            logger.info(f"🔄 Processing file {i}/{len(files)}: {file_path.name}")
            logger.info(f"   📁 Full path: {file_path}")

            try:
                text = self.process_document(file_path)

                if text:
                    # Create text filename (replace extension with .txt)
                    text_filename = file_path.stem + ".txt"
                    text_file_path = output_category_dir / text_filename

                    # Save immediately
                    logger.info(f"   💾 Saving immediately to: {text_file_path}")
                    with open(text_file_path, "w", encoding="utf-8") as f:
                        f.write(text)

                    logger.info(
                        f"✅ SUCCESS: Extracted and saved {len(text)} characters from {file_path.name}"
                    )
                    success_count += 1
                else:
                    logger.warning(
                        f"❌ FAILED: No text extracted from {file_path.name}"
                    )
            except Exception as e:
                logger.error(f"❌ ERROR: Exception processing {file_path.name}: {e}")
                logger.error(f"   🔍 Exception type: {type(e).__name__}")
                continue

        logger.info(f"")
        logger.info(
            f"📊 Category '{category}' summary: {success_count}/{len(files)} files processed successfully"
        )
        return success_count

    def extract_all_texts(self) -> bool:
        """
        Extract text from all documents in all categories.

        Returns:
            True if successful, False otherwise
        """
        logger.info("🚀 Starting text extraction process")

        # Initialize OCR
        if not self.initialize_ocr():
            return False

        # Discover categories
        categories = self.discover_categories()
        if not categories:
            logger.error("No categories found")
            return False

        # Process each category
        total_files_processed = 0

        for category in categories:
            logger.info(f"")
            logger.info(f"📂 Processing category: {category}")
            logger.info(f"=" * 50)

            # Extract texts for this category (saves immediately)
            files_processed = self.extract_text_for_category(category)
            total_files_processed += files_processed

            logger.info(
                f"✅ Category '{category}' complete: {files_processed} files processed"
            )

        logger.info(f"")
        logger.info(f"🎉 Text extraction completed!")
        logger.info(f"📊 Total files processed: {total_files_processed}")

        return True


def main():
    """Main function."""
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
        print("✅ Text extraction completed successfully!")
        print(f"📁 Texts saved to: {document_dataset_path}")
        print("🚀 You can now train the classifier with the extracted texts")
    else:
        print("❌ Text extraction failed!")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
