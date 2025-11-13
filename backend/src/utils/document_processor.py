"""
Document processor for executing the document processing pipeline.
Pure text processing - no database operations, no OCR.
Handles the sequential steps: Classification → NER → Embedding → FAISS
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import config as config
from src.models.shared import OCRPage
from sqlmodel import Session
from src.ml.classification.base_classifier import DocumentClassifier
from src.ml.faiss.embeddings import EmbeddingsIndex
from src.ml.ner.base_ner import NERModel
from src.models.database import EmbeddingMetadata, Entity

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""
    category: str
    confidence: float
    entities: List[Dict[str, Any]]  # All entities from all pages
    aggregated_text: str  # Combined text from all pages
    classification_details: Dict[str, Any]


class DocumentProcessor:
    """
    Pure text processor - handles document processing pipeline without database operations or OCR.
    Executes the sequential steps: Classification → NER → Embedding → FAISS
    """

    def __init__(
        self,
        document_classifier: DocumentClassifier,
        ner_model: Optional[NERModel] = None,
        embeddings_index: Optional[EmbeddingsIndex] = None,
        db: Optional[Session] = None,
    ):
        """
        Initialize the document processor.

        Args:
            document_classifier: Document classifier
            ner_model: Optional NER model for entity extraction
            embeddings_index: Optional FAISS embeddings index
            db: Optional database session for storing FAISS metadata
        """
        self.document_classifier = document_classifier
        self.ner_model = ner_model
        self.embeddings_index = embeddings_index
        self.db = db

    def process(
        self,
        pages: List[Any],  # List[OCRPage] - using Any to avoid circular import
        filename: str,
        document_id: str,
    ) -> ProcessingResult:
        """
        Process pages through the complete pipeline.
        Pure text processing - no database operations, no OCR.

        Args:
            pages: List of OCRPage objects (with page_number, text, etc.)
            filename: Document filename for context
            document_id: Document ID (for FAISS indexing)

        Returns:
            ProcessingResult with all processing results

        Raises:
            Exception: If processing fails at any step
        """
        if not pages:
            raise Exception("No pages provided for processing")

        # Aggregate text for classification (classifiers expect aggregated text)
        aggregated_text = "\n".join([page.text for page in pages])
        if not aggregated_text or not aggregated_text.strip():
            raise Exception("No text provided for processing")

        logger.info(
            f"Starting text processing: {len(pages)} pages "
            f"({len(aggregated_text)} characters total)"
        )

        # ========== STEP 1: Classification ==========
        logger.info(f"[Step 1/4] Starting classification")
        # Prepare page texts for classifier (list of (text, page_number) tuples)
        page_texts = [(page.text, page.page_number) for page in pages]
        category, confidence, _, classification_details = self.document_classifier.classify_document(
            page_texts, filename
        )

        logger.info(f"[Step 1/4] Classification complete: {category} (confidence: {confidence:.3f})")

        # Apply "other" catch-all logic for low confidence
        final_category = self._apply_classification_filters(
            category, confidence, classification_details
        )

        # Skip NER and FAISS if classification is "other" (low confidence/uncertain)
        if final_category == "other":
            logger.info(
                f"Classification is 'other' (low confidence: {confidence:.3f}), "
                f"skipping NER and FAISS indexing"
            )
            return ProcessingResult(
                category=final_category,
                confidence=confidence,
                entities=[],
                aggregated_text=aggregated_text,
                classification_details=classification_details,
            )

        # ========== STEP 2-4: NER and FAISS indexing (per page) ==========
        logger.info(f"[Step 2/4] Starting NER extraction for document type: {final_category}")
        all_entities: List[Dict[str, Any]] = []

        for page in pages:
            page_entities = self._process_page(
                page=page,
                document_id=document_id,
                category=final_category,
            )
            all_entities.extend(page_entities)


        logger.info(
            f"Text processing complete: {final_category} (confidence: {confidence:.3f}), "
            f"{len(all_entities)} entities extracted across {len(pages)} pages"
        )

        return ProcessingResult(
            category=final_category,
            confidence=confidence,
            entities=all_entities,
            aggregated_text=aggregated_text,
            classification_details=classification_details,
        )

    def _process_page(
        self,
        page: OCRPage,  # OCRPage
        document_id: str,
        category: str,
    ) -> List[Dict[str, Any]]:
        """
        Process a single page: NER extraction and FAISS indexing.
        
        Args:
            page: OCRPage object with page text and metadata
            document_id: Document ID
            category: Document classification category
            
        Returns:
            List of entities extracted from this page
        """
        page_entities: List[Dict[str, Any]] = []
        
        # ========== STEP 2: Extract NER entities for this page ==========
        if self.ner_model:
            ner_result = self.ner_model.extract_entities(page.text, category)
            page_entities = [entity.to_dict() for entity in ner_result.entities]
            logger.debug(
                f"[Step 2/4] Page {page.page_number}: extracted {len(page_entities)} entities"
            )
        else:
            logger.debug(f"[Step 2/4] Page {page.page_number}: NER model not available, skipping")
        
        # ========== STEP 3: FAISS indexing (per page) ==========
        if self.embeddings_index:
            logger.debug(f"[Step 3/4] Page {page.page_number}: Adding to FAISS index")
            # Add page to FAISS index
            indices = self.embeddings_index.add([page.text])
            faiss_index = indices[0] if indices else None
            
            # ========== STEP 4: Update metadata (per page) ==========
            if faiss_index is not None:
                logger.debug(f"[Step 4/4] Page {page.page_number}: Storing metadata (FAISS index: {faiss_index})")
                self._update_metadata(
                    document_id=document_id,
                    faiss_index=faiss_index,
                    page_number=page.page_number,
                    text=page.text,
                    category=category,
                    entities=page_entities,
                )
            else:
                logger.warning(f"[Step 3/4] Page {page.page_number}: Failed to get FAISS index")
        else:
            logger.debug(f"[Step 3/4] Page {page.page_number}: FAISS index not available, skipping")
        
        return page_entities


    def _apply_classification_filters(
        self, category: str, confidence: float, classification_details: Dict[str, Any]
    ) -> str:
        """
        Apply classification filters (confidence threshold, uncertainty check).
        Centralized filtering logic for all classifiers - applies "other" category
        as fallback for low confidence or uncertain predictions.

        Args:
            category: Initial predicted category from classifier
            confidence: Classification confidence score
            classification_details: Full classification details including category_probabilities

        Returns:
            Final category after applying filters (may be "other" if filters trigger)
        """
        final_category = category

        # Check confidence threshold
        if confidence < config.CLASSIFIER_CONFIDENCE_THRESHOLD:
            logger.warning(
                f"Confidence {confidence:.3f} below threshold "
                f"{config.CLASSIFIER_CONFIDENCE_THRESHOLD}. "
                f"Using 'other' category instead of {category}."
            )
            return "other"

        # Check for uncertainty (difference between top 2 probabilities)
        # If the top two categories are too close, the model is uncertain
        try:
            category_probs = classification_details.get("category_probabilities", {})
            if category_probs:
                sorted_probs = sorted(category_probs.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_probs) >= 2:
                    top_prob = sorted_probs[0][1]
                    second_prob = sorted_probs[1][1]
                    prob_difference = top_prob - second_prob

                    if prob_difference < config.CLASSIFIER_UNCERTAINTY_MARGIN:
                        logger.warning(
                            f"Uncertainty detected: top={sorted_probs[0][0]}({top_prob:.3f}) vs "
                            f"second={sorted_probs[1][0]}({second_prob:.3f}), "
                            f"diff={prob_difference:.3f} < {config.CLASSIFIER_UNCERTAINTY_MARGIN}. "
                            f"Using 'other' category instead."
                        )
                        return "other"
        except Exception as e:
            logger.error(f"Could not check uncertainty: {e}, using best classification")

        return final_category

    def _update_metadata(
        self,
        document_id: str,
        faiss_index: int,
        page_number: int,
        text: str,
        category: str,
        entities: List[Dict[str, Any]],
    ) -> None:
        """
        Update metadata in database for a FAISS embedding (page-level).

        Args:
            document_id: Document ID
            faiss_index: Position in FAISS index
            page_number: Page number (0-indexed)
            text: The text content for this page
            category: Document classification category
            entities: List of extracted named entities (as dictionaries) for this page
        """
        if not self.db:
            logger.warning("Database session not available, metadata not saved")
            return

        try:
            # Create metadata record for this page
            metadata = EmbeddingMetadata(
                document_id=document_id,
                faiss_index=faiss_index,
                page_number=page_number,
                text=text,
                category=category,
            )
            self.db.add(metadata)
            self.db.flush()  # Flush to get the metadata ID
            
            # Create entity records for this page
            if entities:
                entity_objects = [
                    Entity(
                        embedding_metadata_id=metadata.id,
                        text=entity.get("text", "")[:500],  # Truncate to max length
                        label=entity.get("label", "")[:50],  # Truncate to max length
                        start=entity.get("start", 0),
                        end=entity.get("end", 0),
                        confidence=entity.get("confidence"),
                    )
                    for entity in entities
                ]
                self.db.add_all(entity_objects)
            
            self.db.commit()
            logger.debug(
                f"Added metadata for document {document_id}, page {page_number}, "
                f"FAISS index {faiss_index} with {len(entities)} entities"
            )
        except Exception as e:
            logger.warning(f"Failed to update metadata: {e}")
            self.db.rollback()
            raise

