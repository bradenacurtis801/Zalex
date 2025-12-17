"""
Document processor for executing the document processing pipeline.
Pure text processing - no database operations, no OCR.
Handles the sequential steps: Classification → NER → Embedding → FAISS
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import config as config
from src.models.shared import OCRPage
from sqlmodel import Session
from src.ml.classification.base_classifier import DocumentClassifier
from src.ml.faiss.embeddings import EmbeddingsIndex
from src.ml.ner.base_ner import NERModel, Entity
from src.models.database import EmbeddingMetadata
from src.utils.normalizers import should_normalize_entity, normalize_date

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
        pages: List[OCRPage],  # List[OCRPage] - using Any to avoid circular import
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
    ) -> List[Entity]:
        """
        Process a single page: NER extraction and FAISS indexing.
        
        Args:
            page: OCRPage object with page text and metadata
            document_id: Document ID
            category: Document classification category
            
        Returns:
            List of entities extracted from this page
        """
        page_entities: List[Entity] = []

        # ========== STEP 2: Extract NER entities for this page ==========
        if self.ner_model:
            # Prefer per-line NER to match training (training uses lines).
            # Map line-relative offsets to page-level offsets so metadata remains page-scoped.
            try:
                page_text = page.text or ""
                cursor = 0

                for ocr_line in page.ocr_result.lines:
                    line_text = (ocr_line.text or "").strip()
                    if not line_text:
                        continue

                    # Try to find exact line match starting at the current cursor
                    idx = page_text.find(line_text, cursor)
                    if idx == -1:
                        # Fallback: try finding anywhere in the page
                        idx = page_text.find(line_text)

                    if idx == -1:
                        # As a last resort, try a collapsed-whitespace match
                        collapsed_page = re.sub(r"\s+", " ", page_text).strip()
                        collapsed_line = re.sub(r"\s+", " ", line_text).strip()
                        cidx = collapsed_page.find(collapsed_line)
                        if cidx != -1:
                            # map collapsed index back approximately by searching nearby
                            # (best-effort; if mapping fails, skip this line)
                            approx = page_text.find(collapsed_line)
                            idx = approx if approx != -1 else -1

                    if idx == -1:
                        logger.debug(
                            f"[Step 2/4] Page {page.page_number}: could not map line to page text, skipping line: '{line_text[:40]}'"
                        )
                        continue

                    line_start = idx
                    line_end = idx + len(line_text)
                    cursor = line_end

                    ner_result = self.ner_model.extract_entities(line_text, category)
                    for ent in ner_result.entities:
                        # Map relative offsets to page-level offsets
                        rel_start = ent.start
                        rel_end = ent.end
                        ent.start = line_start + rel_start
                        ent.end = line_start + rel_end
                        ent.page_number = page.page_number
                        # Ensure text and label keys exist
                        ent.text = page_text[ent.start:ent.end]
                        # Normalize DATE entities when appropriate and store ISO value
                        try:
                            if should_normalize_entity(ent, min_confidence=0.0):
                                iso = normalize_date(ent.text)
                                if iso:
                                    ent.normalized = iso
                        except Exception:
                            # Normalization must not break processing; ignore failures
                            pass
                        page_entities.append(ent)

                # Deduplicate identical spans (start, end, label)
                seen = set()
                unique_entities: List[Entity] = []
                for e in page_entities:
                    key = (e.start, e.end, e.label)
                    if key in seen:
                        continue
                    seen.add(key)
                    unique_entities.append(e)
                page_entities = unique_entities
                # Ensure DATE entities are normalized even when page-level NER was used
                try:
                    self._apply_normalization_to_entities(page_entities)
                except Exception:
                    # Never let normalization break processing
                    logger.debug("Date normalization failed for page_entities, continuing without normalized values")

                logger.debug(
                    f"[Step 2/4] Page {page.page_number}: extracted {len(page_entities)} entities (per-line)"
                )
            except Exception as e:
                logger.warning(f"NER per-line processing failed, falling back to page-level NER: {e}")
                try:
                    ner_result = self.ner_model.extract_entities(page.text, category)
                    page_entities = [entity.to_dict() for entity in ner_result.entities]
                except Exception:
                    page_entities = []
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

    def _apply_normalization_to_entities(self, entities: List[Entity]) -> None:
        """Apply normalization (ISO date) to DATE entities in-place.

        This is a best-effort step that will not raise on failure. It uses the
        existing should_normalize_entity / normalize_date helpers.
        """
        if not entities:
            return

        for ent in entities:
            try:
                # Skip if already normalized
                if ent.normalized:
                    continue

                # Only attempt normalization for entities that qualify
                if should_normalize_entity(ent, min_confidence=0.0):
                    iso = normalize_date(ent.text)
                    if iso:
                        ent.normalized = iso
            except Exception:
                # Ignore normalization errors per-page to avoid breaking pipeline
                continue


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
        entities: List[Entity],
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
                        text=entity.text[:500],  # Truncate to max length
                        label=entity.label[:50],  # Truncate to max length
                        start=entity.start,
                        end=entity.end,
                        confidence=entity.confidence,
                        normalized_value=entity.normalized,
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

