"""
Document processing service for OCR, text extraction, and indexing.
"""

import json
import logging
import os
import re
import string
import sys

import config as config
import faiss
import fitz
import numpy as np
import pytesseract
from PIL import Image
from pytesseract import TesseractNotFoundError
from sentence_transformers import SentenceTransformer
from src.core.exceptions import DocumentProcessingException, OCRNotAvailableException
from src.ml.classification.base_classifier import BaseDocumentClassifier
from src.ocr.ocr_reader import extract_text_from_bytes, extract_text_from_image

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document processing, OCR, and indexing operations."""

    def __init__(
        self,
        model: SentenceTransformer,
        index: faiss.IndexFlatL2,
        metadata: list,
        document_classifier=None,
        category_metadata: dict = None,
    ):
        self.model = model
        self.index = index
        self.metadata = metadata
        self.document_classifier = document_classifier
        self.category_metadata = category_metadata or {}

        # Initialize category metadata with model categories if available
        if self.document_classifier and self.document_classifier.is_available():
            model_categories = self.document_classifier.get_supported_categories()
            for category in model_categories:
                if category not in self.category_metadata:
                    self.category_metadata[category] = []

    def process_document(self, file_path: str, filename: str) -> dict:
        """
        Processes a single document (PDF or image), extracts text, creates embeddings,
        and adds them to the FAISS index.

        Args:
            file_path: Path to the uploaded file
            filename: Name of the file

        Returns:
            dict: Status and message of the processing operation
        """
        logger.debug(f"Starting document processing for {filename}")
        logger.debug(f"File path: {file_path}")
        logger.debug(f"File size: {os.path.getsize(file_path)} bytes")

        texts_to_index = []

        file_extension = os.path.splitext(filename)[1].lower()
        logger.debug(f"File extension: {file_extension}")

        if file_extension == ".pdf":
            logger.info(f"Processing PDF: {filename}")
            doc = fitz.open(file_path)
            total_pages = len(doc)
            logger.debug(f"PDF has {total_pages} pages")

            for page_num, page in enumerate(doc):
                logger.debug(f"Processing page {page_num + 1}/{total_pages}")

                # Convert PDF page to an image (pixmap)
                logger.debug(f"Converting page {page_num + 1} to image...")
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                logger.debug(
                    f"Page {page_num + 1} converted to image. Size: {len(img_bytes)} bytes"
                )

                # Perform OCR on the image bytes
                logger.debug(f"Starting OCR on page {page_num + 1}...")
                try:
                    # Extract text directly from bytes using the OCR engine
                    text = extract_text_from_bytes(img_bytes, "png", "eng+spa")
                    ocr_results = [text] if text.strip() else []

                    logger.debug(
                        f"OCR completed on page {page_num + 1}. Found {len(ocr_results)} text chunks"
                    )
                except Exception as ocr_error:
                    logger.error(f"OCR failed on page {page_num + 1}: {ocr_error}")
                    logger.debug(f"Continuing with next page...")
                    continue

                for i, text_chunk in enumerate(ocr_results):
                    logger.debug(
                        f"Processing text chunk {i+1}/{len(ocr_results)} from page {page_num + 1}"
                    )
                    texts_to_index.append(
                        {
                            "text": text_chunk,
                            "source": filename,
                            "page": page_num + 1,
                        }
                    )

                logger.debug(
                    f"Page {page_num + 1} processing complete. Total chunks so far: {len(texts_to_index)}"
                )

            doc.close()
            logger.debug(
                f"PDF processing complete. Total text chunks extracted: {len(texts_to_index)}"
            )

        elif file_extension in [".jpg", ".jpeg", ".png"]:
            logger.info(f"Processing image: {filename}")
            # Perform OCR directly on the image file
            try:
                ocr_results = self.get_unique_words_from_image(file_path)
                for text_chunk in ocr_results:
                    texts_to_index.append(
                        {"text": text_chunk, "source": filename, "page": 1}
                    )
                logger.info(
                    f"OCR completed for {filename}. Extracted {len(ocr_results)} text chunks."
                )
            except Exception as e:
                logger.warning(f"OCR failed for {filename}: {e}")
                # Still try to classify with empty text - classifier might still work
                texts_to_index.append({"text": "", "source": filename, "page": 1})
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return {"status": "error", "message": "Unsupported file type"}

        if not texts_to_index:
            raise DocumentProcessingException(
                f"No text could be extracted from {filename}"
            )

        # Perform document classification
        document_category, confidence = self._classify_document(
            texts_to_index, filename
        )
        logger.info(
            f"Document {filename} classified as: {document_category} (confidence: {confidence:.3f})"
        )

        # Create embeddings for the extracted text chunks
        logger.info(
            f"Creating embeddings for {len(texts_to_index)} text chunks from {filename}."
        )
        text_contents = [item["text"] for item in texts_to_index]
        logger.debug(
            f"Text contents sample: {text_contents[0][:100] if text_contents else 'No text'}..."
        )

        logger.debug("Starting embedding creation...")
        embeddings = self.model.encode(text_contents, convert_to_tensor=False)
        logger.debug(f"Embeddings created. Shape: {embeddings.shape}")

        # Add embeddings to FAISS index and update metadata
        logger.debug("Adding embeddings to FAISS index...")
        self.index.add(np.array(embeddings).astype("float32"))
        logger.debug(
            f"Embeddings added to index. Index now has {self.index.ntotal} total vectors"
        )

        logger.debug("Updating metadata...")
        for item in texts_to_index:
            # Add classification information to each text chunk
            item["category"] = document_category
            item["confidence"] = confidence
            self.metadata.append(item)
        logger.debug(f"Metadata updated. Total metadata entries: {len(self.metadata)}")

        # Update category metadata
        self._update_category_metadata(
            filename, file_path, document_category, confidence
        )

        logger.info(
            f"Successfully added {len(embeddings)} vectors to the index for {filename}."
        )
        logger.debug("Saving index and metadata to disk...")
        self.save_index_and_metadata()
        self.save_category_metadata()
        logger.debug("Index and metadata saved successfully")
        return {"status": "success", "message": f"Successfully indexed {filename}."}

    def get_unique_words_from_image(self, image_path: str) -> list[str]:
        """
        Performs OCR on an image, processes the text to extract unique words,
        and returns them as a sorted list.

        This function replicates the shell command:
        tesseract <image> stdout -l spa+eng | tr '[:punct:]' ' ' | tr -s ' ' '\n' | sort -u

        Args:
            image_path: The file path to the image.

        Returns:
            A list of unique, sorted words found in the image.
            Returns an empty list if the image cannot be opened or processed.
        """
        try:
            # Step 1: Perform OCR using pytesseract
            # This is equivalent to `tesseract your_image.png stdout -l spa+eng`
            # The 'lang' argument handles both Spanish and English.
            raw_text = pytesseract.image_to_string(
                Image.open(image_path), lang="spa+eng"
            )

            # --- Text Processing Steps ---

            # Make text lowercase to ensure case-insensitive uniqueness (like `sort -u`)
            text = raw_text.lower()

            # Step 2: Replace all punctuation with a space
            # This is equivalent to `tr '[:punct:]' ' '`
            # We use a regular expression for a robust replacement.
            text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)

            # Step 3: Split the text into words
            # This is equivalent to `tr -s ' ' '\n'`
            # The .split() method naturally handles multiple spaces between words.
            words = text.split()

            # Step 4: Get a unique, sorted list of words
            # This is equivalent to `sort -u`
            # A `set` stores only unique items, and `sorted()` sorts them.
            unique_sorted_words = sorted(list(set(words)))

            return unique_sorted_words

        except FileNotFoundError:
            raise DocumentProcessingException(f"Image file not found: {image_path}")
        except TesseractNotFoundError as e:
            # TesseractNotFoundError is thrown when tesseract is not installed or not in PATH
            raise OCRNotAvailableException(f"Tesseract OCR is not available: {str(e)}")
        except Exception as e:
            raise DocumentProcessingException(f"OCR processing failed: {str(e)}")

    def save_index_and_metadata(self):
        """Saves the current FAISS index and metadata to disk."""
        logger.info(f"Saving FAISS index to {config.INDEX_FILE}")
        faiss.write_index(self.index, str(config.INDEX_FILE))
        logger.info(f"Saving metadata to {config.METADATA_FILE}")
        with open(config.METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=4)
        logger.info("Index and metadata saved successfully.")

    def _classify_document(self, texts_to_index: list, filename: str) -> tuple:
        """
        Classify a document based on its extracted text content.

        Args:
            texts_to_index: List of text chunks from the document
            filename: Name of the file being processed

        Returns:
            Tuple of (category, confidence_score)
        """
        if not self.document_classifier or not self.document_classifier.is_available():
            logger.warning("Document classifier not available, using 'other' category")
            return "other", 0.0

        try:
            # Combine all text chunks for classification
            combined_text = " ".join([item["text"] for item in texts_to_index])

            # Truncate text if too long (classifier has max length)
            if len(combined_text) > 2000:  # Conservative limit
                combined_text = combined_text[:2000]
                logger.debug(f"Text truncated to 2000 characters for classification")

            # Use generic classifier interface
            if isinstance(self.document_classifier, BaseDocumentClassifier):
                result = self.document_classifier.classify(combined_text, filename)
                category = result.category
                confidence = result.confidence
                logger.debug(f"Classification method: {result.method}")
            else:
                # Fallback for old interface
                category, confidence = self.document_classifier.classify(combined_text)

            # Map classifier output to our category names
            # Use the actual categories from the trained model dynamically
            if self.document_classifier and self.document_classifier.is_available():
                # Get categories from the trained model
                model_categories = self.document_classifier.get_supported_categories()
                # Create mapping that preserves the original category names
                category_mapping = {cat: cat for cat in model_categories}
                category_mapping["other"] = "other"  # Always include "other"
            else:
                # Fallback if classifier not available
                category_mapping = {"other": "other"}

            mapped_category = category_mapping.get(category, "other")
            logger.debug(
                f"Raw classification: {category} -> Mapped to: {mapped_category}"
            )

            return mapped_category, confidence

        except Exception as e:
            logger.error(f"Classification failed for {filename}: {e}")
            return "other", 0.0

    def _update_category_metadata(
        self, filename: str, file_path: str, category: str, confidence: float
    ):
        """
        Update the category metadata with the new document.

        Args:
            filename: Name of the file
            file_path: Full path to the file
            category: Document category
            confidence: Classification confidence score
        """
        try:
            # Create document entry
            document_entry = {
                "filename": filename,
                "file_path": file_path,
                "category": category,
                "confidence": confidence,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            }

            # Add to appropriate category list
            if category in self.category_metadata:
                self.category_metadata[category].append(document_entry)
            else:
                # If category doesn't exist, add to 'other'
                self.category_metadata.setdefault("other", []).append(document_entry)
                logger.warning(
                    f"Unknown category '{category}' for {filename}, added to 'other'"
                )

            logger.debug(f"Added {filename} to category '{category}' in metadata")

        except Exception as e:
            logger.error(f"Failed to update category metadata for {filename}: {e}")

    def save_category_metadata(self):
        """Saves the current category metadata to disk."""
        category_file = config.APP_DIR / "category_metadata.json"
        logger.info(f"Saving category metadata to {category_file}")
        with open(category_file, "w", encoding="utf-8") as f:
            json.dump(self.category_metadata, f, indent=4)
        logger.info("Category metadata saved successfully.")
