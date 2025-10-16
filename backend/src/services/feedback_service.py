"""Feedback service for handling user corrections and model updates."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import config
import numpy as np
from sentence_transformers import SentenceTransformer
from src.core.exceptions import (
    CategoryNotFoundError,
    DocumentNotFoundError,
    FeedbackException,
)
from src.ml.classification.base_classifier import BaseDocumentClassifier
from src.models.feedback import (
    FeedbackSummary,
    ReclassificationRequest,
    ReclassificationResponse,
)

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for handling user feedback and model corrections."""

    def __init__(
        self,
        document_classifier: BaseDocumentClassifier,
        category_metadata: dict,
        model_path: str,
    ):
        self.document_classifier = document_classifier
        self.category_metadata = category_metadata
        self.model_path = model_path
        self.feedback_file = config.APP_DIR / "feedback_log.json"
        self.feedback_data = self._load_feedback_data()

    def _load_feedback_data(self) -> Dict:
        """Load existing feedback data from disk."""
        if self.feedback_file.exists() and self.feedback_file.stat().st_size > 0:
            try:
                with open(self.feedback_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load feedback data: {e}")
                return self._create_empty_feedback_data()
        return self._create_empty_feedback_data()

    def _create_empty_feedback_data(self) -> Dict:
        """Create empty feedback data structure."""
        return {
            "corrections": [],
            "corrections_by_category": {},
            "model_updates": [],
            "last_updated": datetime.now().isoformat(),
            "version": "1.0.0",
        }

    def _save_feedback_data(self):
        """Save feedback data to disk."""
        try:
            self.feedback_data["last_updated"] = datetime.now().isoformat()
            with open(self.feedback_file, "w", encoding="utf-8") as f:
                json.dump(self.feedback_data, f, indent=2)
            logger.info("Feedback data saved successfully")
        except Exception as e:
            logger.error(f"Failed to save feedback data: {e}")

    def process_reclassification(
        self, request: ReclassificationRequest
    ) -> ReclassificationResponse:
        """
        Process a document reclassification request.

        Args:
            request: Reclassification request with document details

        Returns:
            ReclassificationResponse with processing results
        """
        try:
            logger.info(
                f"Processing reclassification: {request.filename} from {request.current_category} to {request.new_category}"
            )

            # Validate the new category
            available_categories = self._get_available_categories()
            if request.new_category not in available_categories:
                # If category doesn't exist, add it to 'other'
                request.new_category = "other"
                logger.info(
                    f"Category '{request.new_category}' not found, using 'other'"
                )

            # Update the document in category metadata
            success = self._update_document_category(request)

            if success:
                # Log the correction
                self._log_correction(request)

                # Update model if we have enough corrections
                model_updated = self._should_update_model()

                # Get updated categories
                updated_categories = self._get_available_categories()

                return ReclassificationResponse(
                    success=True,
                    message=f"Document reclassified from {request.current_category} to {request.new_category}",
                    updated_categories=updated_categories,
                    model_updated=model_updated,
                )
            else:
                return ReclassificationResponse(
                    success=False, message="Failed to reclassify document"
                )

        except Exception as e:
            logger.error(f"Error processing reclassification: {e}")
            return ReclassificationResponse(
                success=False, message=f"Error processing reclassification: {str(e)}"
            )

    def _get_available_categories(self) -> List[str]:
        """Get list of available categories from the model."""
        try:
            if self.document_classifier and self.document_classifier.is_initialized:
                return self.document_classifier.get_supported_categories()
            else:
                # Fallback to category metadata
                return list(self.category_metadata.keys())
        except Exception as e:
            logger.error(f"Error getting available categories: {e}")
            return ["other"]

    def _update_document_category(self, request: ReclassificationRequest) -> bool:
        """Update the document's category in the metadata."""
        try:
            # Find and update the document in category metadata
            category_metadata = self.category_metadata

            # Find the document in the current category first
            if request.current_category not in category_metadata:
                raise CategoryNotFoundError(
                    f"Category '{request.current_category}' not found"
                )

            if request.filename not in category_metadata[request.current_category]:
                raise DocumentNotFoundError(
                    f"Document '{request.filename}' not found in category '{request.current_category}'"
                )

            # Get the document entry - now guaranteed to exist
            document_entry = category_metadata[request.current_category][
                request.filename
            ]

            # Update the document entry
            document_entry["category"] = request.new_category
            document_entry["timestamp"] = datetime.now().isoformat()
            if request.confidence is not None:
                document_entry["confidence"] = request.confidence

            # Remove from current category
            del category_metadata[request.current_category][request.filename]

            # Add to new category
            if request.new_category not in category_metadata:
                category_metadata[request.new_category] = {}
            category_metadata[request.new_category][request.filename] = document_entry

            # Save updated metadata (this would need to be injected or handled differently)
            # For now, we'll skip this as it requires access to app_state methods
            logger.info(
                "Category metadata updated (save not implemented in refactored version)"
            )
            logger.info(
                f"Document {request.filename} moved from {request.current_category} to {request.new_category}"
            )
            return True

        except (CategoryNotFoundError, DocumentNotFoundError) as e:
            # Re-raise domain-specific exceptions
            raise e
        except Exception as e:
            logger.error(f"Unexpected error updating document category: {e}")
            raise FeedbackException(f"Failed to update document category: {str(e)}")

    def _log_correction(self, request: ReclassificationRequest):
        """Log the correction for tracking and model updates."""
        from ..models.feedback import CorrectionData

        correction = CorrectionData(
            filename=request.filename,
            from_category=request.current_category,
            to_category=request.new_category,
            confidence=request.confidence,
            user_comment=request.user_comment,
            timestamp=datetime.now().isoformat(),
        )

        self.feedback_data["corrections"].append(correction)

        # Update corrections by category
        if request.new_category not in self.feedback_data["corrections_by_category"]:
            self.feedback_data["corrections_by_category"][request.new_category] = 0
        self.feedback_data["corrections_by_category"][request.new_category] += 1

        self._save_feedback_data()

    def _should_update_model(self) -> bool:
        """Determine if the model should be updated based on feedback."""
        # Update model every 10 corrections or if it's been a while
        correction_count = len(self.feedback_data["corrections"])

        # Check if we have enough corrections
        if correction_count % 10 == 0 and correction_count > 0:
            logger.info(f"Triggering model update after {correction_count} corrections")
            return self._update_model_embeddings()

        return False

    def _update_model_embeddings(self) -> bool:
        """Update the model embeddings based on feedback corrections."""
        try:
            # Check if classifier supports retraining
            if (
                not self.document_classifier
                or not self.document_classifier.is_initialized
            ):
                logger.error("No classifier available for retraining")
                return False

            logger.info("Updating model embeddings using classifier retraining...")

            # Process all corrections since the last model update
            corrections_to_process = self.feedback_data["corrections"].copy()

            # Use the classifier's own retraining method
            success = self.document_classifier.retrain_with_corrections(
                corrections_to_process, self.model_path
            )

            if not success:
                logger.error("Failed to update model embeddings")
                return False

            # Log the model update
            model_update = {
                "timestamp": datetime.now().isoformat(),
                "corrections_processed": len(corrections_to_process),
                "total_corrections": len(self.feedback_data["corrections"]),
                "classifier_type": self.document_classifier.__class__.__name__,
            }
            self.feedback_data["model_updates"].append(model_update)

            # Remove the corrections that were used for this model update
            corrections_to_remove = len(corrections_to_process)
            self.feedback_data["corrections"] = self.feedback_data["corrections"][
                corrections_to_remove:
            ]

            # Recalculate corrections by category for remaining corrections
            self.feedback_data["corrections_by_category"] = {}
            for correction in self.feedback_data["corrections"]:
                category = correction["to_category"]
                if category not in self.feedback_data["corrections_by_category"]:
                    self.feedback_data["corrections_by_category"][category] = 0
                self.feedback_data["corrections_by_category"][category] += 1

            self._save_feedback_data()

            logger.info(
                f"Model embeddings update completed using {self.document_classifier.__class__.__name__}. "
                f"Removed {corrections_to_remove} processed corrections. "
                f"Remaining corrections: {len(self.feedback_data['corrections'])}"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating model embeddings: {e}")
            return False

    def get_feedback_summary(self) -> FeedbackSummary:
        """Get a summary of feedback corrections."""
        corrections_by_category = self.feedback_data.get("corrections_by_category", {})
        total_corrections = len(self.feedback_data.get("corrections", []))
        last_updated = self.feedback_data.get(
            "last_updated", datetime.now().isoformat()
        )
        model_version = self.feedback_data.get("version", "1.0.0")

        return FeedbackSummary(
            total_corrections=total_corrections,
            corrections_by_category=corrections_by_category,
            last_updated=datetime.fromisoformat(last_updated),
            model_version=model_version,
        )
