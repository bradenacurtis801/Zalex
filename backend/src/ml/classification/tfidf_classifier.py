"""
TF-IDF + Naive Bayes classifier for inference.
Uses a trained MultinomialNB model with TfidfVectorizer for document classification.
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
from huggingface_hub import snapshot_download, hf_hub_download
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

if TYPE_CHECKING:
    from src.models.schemas.feedback import CorrectionData

from scanpro_lib.utils.text_preprocessing import TextCleaner
from .base_classifier import DocumentClassifier, DocumentClassificationResult
from scanpro_lib.models.classifier import TFIDFClassifierModel

logger = logging.getLogger(__name__)


class PreTrainedTFIDFClassifier(DocumentClassifier):
    """
    Pre-trained TF-IDF + Naive Bayes classifier for inference only.
    Loads a trained MultinomialNB model and TfidfVectorizer for classification.
    """

    def __init__(
        self,
        model_name_or_path: str,
        cache_folder: Optional[str] = None,
        token: Union[bool, str, None] = None,
    ):
        super().__init__(model_name_or_path, cache_folder, token)
        self.model: Optional[MultinomialNB] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.class_names: List[str] = []
        self.id2label: Dict[int, str] = {}
        self.label2id: Dict[str, int] = {}
        self.model_name: str = ""
        self.model_path: str = ""
        self.vectorizer_path: str = ""
        self.classifier_model: Optional[TFIDFClassifierModel] = None
        
        # Initialize text cleaner (uses same cleaning as training)
        self.text_cleaner = TextCleaner(track_metrics=False)

        # Set up cache folder (same pattern as finetune_classifier)
        if cache_folder is None:
            cache_folder = os.getenv('SENTENCE_TRANSFORMERS_HOME')
            if cache_folder is None:
                try:
                    from torch.hub import _get_torch_home
                    torch_cache_home = _get_torch_home()
                except ImportError:
                    torch_cache_home = os.path.expanduser(
                        os.path.join(os.getenv('XDG_CACHE_HOME', '~/.cache'), 'torch')
                    )
                cache_folder = os.path.join(torch_cache_home, 'sentence_transformers')

        self.cache_folder = cache_folder

        # Handle Hugging Face model ID or local path (same pattern as finetune_classifier)
        if "/" in model_name_or_path and not os.path.exists(model_name_or_path):
            # This looks like a Hugging Face repo ID (e.g., "username/model-name")
            model_path = str(Path(self.cache_folder) / model_name_or_path.replace("/", "-"))
            
            # Check cache for model
            logger.debug(f"Checking cache for model: {model_path}")
            if os.path.exists(model_path):
                self.model_path = model_path
            else:
                logger.debug(f"Model not found in cache, downloading from Hugging Face: {model_name_or_path}")
                # Download model from Hugging Face
                logger.info(f"Loading model from Hugging Face: {model_name_or_path}")
                self.model_path = self._download_from_huggingface(model_name_or_path, model_path, token)
        else:
            # This is a local path
            self.model_path = model_name_or_path

        # Load the model during construction
        logger.info("Loading TF-IDF + Naive Bayes classifier model...")
        self._load_model()
    
    def _download_from_huggingface(
        self, repo_id: str, local_path: str, token: Optional[str] = None
    ) -> str:
        """
        Download model from Hugging Face Hub with caching.
        Same pattern as finetune_classifier.

        Args:
            repo_id: Hugging Face repository ID
            local_path: Local path where model should be downloaded
            token: Hugging Face token for private models

        Returns:
            Local path to downloaded model directory
        """
        try:
            # Download the model
            logger.info(f"Downloading model to: {local_path}")
            model_path = snapshot_download(
                repo_id=repo_id,
                local_dir=local_path,
                token=token,
                local_dir_use_symlinks=False,  # Avoid symlinks for better compatibility
            )
            logger.info(f"Model downloaded to: {model_path}")
            return model_path

        except Exception as e:
            logger.error(f"Failed to download model from Hugging Face {repo_id}: {e}")
            raise

    def _load_model(self) -> None:
        """
        Internal method to load the model during construction.
        Sets is_initialized to True on success, False on failure.
        Uses TFIDFClassifierModel for validation and structure management.
        """
        try:
            model_dir = Path(self.model_path)

            # Use TFIDFClassifierModel to validate and load model structure
            # This handles all validation and file path resolution
            logger.info(f"Validating and loading model structure from: {model_dir}")
            self.classifier_model = TFIDFClassifierModel.from_directory(model_dir)

            # Get file paths from the validated model instance
            model_file = self.classifier_model.classifier_file
            vectorizer_file = self.classifier_model.vectorizer_file

            # Store vectorizer path for reference
            self.vectorizer_path = str(vectorizer_file)

            # Load model and vectorizer using joblib
            logger.info(f"Loading model from: {model_file}")
            self.model = joblib.load(model_file)

            logger.info(f"Loading vectorizer from: {vectorizer_file}")
            self.vectorizer = joblib.load(vectorizer_file)

            # Get class names from the model instance (already loaded by from_directory)
            class_names_data = self.classifier_model.get_class_names()
            self.class_names = class_names_data
            self.id2label = self.classifier_model.get_id2label()
            self.label2id = self.classifier_model.get_label2id()

            self.model_name = os.path.basename(self.model_path)
            self.is_initialized = True

            logger.info(f"Successfully loaded TF-IDF classifier: {self.model_name}")
            logger.info(f"Categories: {self.class_names}")

        except Exception as e:
            logger.error(f"Failed to load TF-IDF classifier model: {e}")
            self.is_initialized = False
            raise


    def _clean_text(self, text: str) -> str:
        """
        Clean text using the same pipeline as training.
        Uses the shared TextCleaner for consistency.
        """
        if not text or not text.strip():
            return ""
        
        # Use the shared TextCleaner (same as training)
        cleaned_text = self.text_cleaner.clean_text(text)
        return cleaned_text

    def load_model(self) -> bool:
        """
        Load a pre-trained TF-IDF + Naive Bayes model from disk.
        This method is provided for backward compatibility.
        The model is automatically loaded during construction.

        Returns:
            bool: True if successful, False otherwise
        """
        # Model is already loaded during construction
        return self.is_initialized

    def initialize(self) -> bool:
        """Initialize the classifier by loading the model."""
        return self.load_model()

    def get_supported_categories(self) -> List[str]:
        """Get list of supported categories."""
        return self.class_names.copy()

    def classify(self, text: str, filename: str = None) -> DocumentClassificationResult:
        """
        Classify text using the TF-IDF + Naive Bayes model.

        Args:
            text: Input text to classify
            filename: Optional filename for context

        Returns:
            DocumentClassificationResult: Classification result
        """
        if not self.is_initialized or self.model is None or self.vectorizer is None:
            return DocumentClassificationResult(
                category="unknown",
                confidence=0.0,
                method="tfidf",
                details={"error": "Classifier not initialized"},
            )

        try:
            # Clean text using the same pipeline as training
            cleaned_text = self._clean_text(text)

            if not cleaned_text or not cleaned_text.strip():
                return DocumentClassificationResult(
                    category="unknown",
                    confidence=0.0,
                    method="tfidf",
                    details={"error": "Text is empty after cleaning", "filename": filename},
                )

            # Transform text to TF-IDF features
            text_vector = self.vectorizer.transform([cleaned_text])

            # Get predictions
            predicted_class_idx = self.model.predict(text_vector)[0]
            predicted_proba = self.model.predict_proba(text_vector)[0]

            # Get predicted category using id2label mapping if available
            predicted_id = int(predicted_class_idx)
            if self.id2label:
                predicted_category = self.id2label.get(predicted_id, "unknown")
            elif predicted_id < len(self.class_names):
                predicted_category = self.class_names[predicted_id]
            else:
                predicted_category = "unknown"

            # Get confidence (probability of predicted class)
            confidence = float(predicted_proba[predicted_id])

            # Get all category probabilities for details
            if self.id2label:
                category_probabilities = {
                    self.id2label.get(i, f"class_{i}"): float(prob)
                    for i, prob in enumerate(predicted_proba)
                }
            else:
                category_probabilities = {
                    (self.class_names[i] if i < len(self.class_names) else f"class_{i}"): float(prob)
                    for i, prob in enumerate(predicted_proba)
                }

            # Extract feature importance (which words/ngrams contributed most to the classification)
            feature_importance = self._get_feature_importance(
                text_vector, predicted_id, cleaned_text
            )

            # Return raw prediction - filtering logic (confidence threshold, uncertainty check)
            # is handled by DocumentProcessor._apply_classification_filters()
            return DocumentClassificationResult(
                category=predicted_category,
                confidence=confidence,
                method="tfidf",
                details={
                    "category_probabilities": category_probabilities,
                    "model_name": self.model_name,
                    "filename": filename,
                    "predicted_class_idx": int(predicted_class_idx),
                    "feature_importance": feature_importance,
                },
            )

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return DocumentClassificationResult(
                category="unknown",
                confidence=0.0,
                method="tfidf",
                details={"error": str(e), "filename": filename},
            )

    def _get_feature_importance(
        self, text_vector, predicted_class_idx: int, original_text: str
    ) -> Dict[str, Any]:
        """
        Extract feature importance to understand which words/ngrams contributed most
        to the classification decision.

        Args:
            text_vector: TF-IDF vectorized text (sparse matrix)
            predicted_class_idx: Index of the predicted class
            original_text: Original cleaned text for context

        Returns:
            Dictionary with top contributing features and their importance scores
        """
        try:
            # Get log probabilities for all classes
            num_classes = len(self.model.classes_)
            log_probs_predicted = self.model.feature_log_prob_[predicted_class_idx]
            
            # Calculate relative importance: how much more likely is this feature
            # in the predicted class compared to the average of other classes
            log_probs_other = np.zeros_like(log_probs_predicted)
            for class_idx in range(num_classes):
                if class_idx != predicted_class_idx:
                    log_probs_other += self.model.feature_log_prob_[class_idx]
            if num_classes > 1:
                log_probs_other /= (num_classes - 1)
            
            # Relative log probability: difference between predicted class and average of others
            # Positive values mean the feature is more indicative of the predicted class
            relative_log_probs = log_probs_predicted - log_probs_other
            
            # Convert sparse matrix to dense array for the input text
            text_vector_dense = text_vector.toarray()[0]
            
            # Calculate contribution: TF-IDF value * relative log probability
            # This shows which features in THIS document are most indicative of the predicted class
            contributions = text_vector_dense * relative_log_probs
            
            # Get feature names (words/ngrams) from vectorizer
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get indices of non-zero features (features present in the text)
            # text_vector is a sparse matrix, convert to CSR format to access indices/data
            text_vector_csr = text_vector.tocsr()
            non_zero_indices = text_vector_csr.indices
            non_zero_values = text_vector_csr.data
            
            # Common stopwords to filter out (these are usually not informative)
            stopwords = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
                "been", "being", "have", "has", "had", "do", "does", "did", "will",
                "would", "could", "should", "may", "might", "must", "can", "this",
                "that", "these", "those", "it", "its", "they", "them", "their"
            }
            
            # Calculate contributions for features present in the text
            feature_contributions = []
            for idx, tfidf_value in zip(non_zero_indices, non_zero_values):
                if idx < len(contributions):
                    contribution = contributions[idx]
                    feature_name = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
                    
                    # Skip very short features and stopwords (unless they have very high contribution)
                    if len(feature_name) < 2 or (feature_name.lower() in stopwords and abs(contribution) < 0.5):
                        continue
                    
                    feature_contributions.append({
                        "feature": feature_name,
                        "contribution": float(contribution),
                        "tfidf_value": float(tfidf_value),
                        "relative_log_probability": float(relative_log_probs[idx]),
                    })
            
            # Sort by contribution (positive = supports classification, negative = opposes it)
            # Focus on positive contributions first, then by absolute value
            feature_contributions.sort(
                key=lambda x: (x["contribution"] < 0, -abs(x["contribution"])),
                reverse=False
            )
            
            # Get top 20 contributing features (prioritize positive contributions)
            top_features = feature_contributions[:20]
            
            # Also find these features in the original text for context
            top_feature_texts = []
            text_lower = original_text.lower()
            for feat_info in top_features[:10]:  # Top 10 for text context
                feature = feat_info["feature"]
                # Try to find the feature in the original text (handle ngrams)
                if " " in feature:
                    # N-gram: search for the phrase
                    if feature in text_lower:
                        # Find context around the feature
                        idx = text_lower.find(feature)
                        start = max(0, idx - 50)
                        end = min(len(original_text), idx + len(feature) + 50)
                        context = original_text[start:end].strip()
                        top_feature_texts.append({
                            "feature": feature,
                            "context": context,
                            "contribution": feat_info["contribution"],
                        })
                else:
                    # Single word: find exact matches (case-insensitive)
                    words = original_text.split()
                    matching_words = [w for w in words if feature.lower() == w.lower()]
                    if not matching_words:
                        # Fallback: partial match
                        matching_words = [w for w in words if feature.lower() in w.lower()]
                    if matching_words:
                        top_feature_texts.append({
                            "feature": feature,
                            "occurrences": matching_words[:5],  # First 5 occurrences
                            "contribution": feat_info["contribution"],
                        })
            
            return {
                "top_contributing_features": [
                    {
                        "feature": f["feature"],
                        "contribution_score": f["contribution"],
                        "tfidf_value": f["tfidf_value"],
                        "relative_importance": f["relative_log_probability"],
                    }
                    for f in top_features
                ],
                "top_features_in_text": top_feature_texts,
                "total_features_analyzed": len(feature_contributions),
                "predicted_class": self.id2label.get(predicted_class_idx, f"class_{predicted_class_idx}") if self.id2label else self.class_names[predicted_class_idx] if predicted_class_idx < len(self.class_names) else "unknown",
            }
            
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
            return {
                "error": str(e),
                "note": "Feature importance extraction failed",
            }

    def get_available_categories(self) -> list:
        """Get list of available categories (alias for get_supported_categories)."""
        return self.get_supported_categories()

    def retrain_with_corrections(
        self, corrections: List["CorrectionData"], model_path: Optional[str] = None
    ) -> bool:
        """
        Retrain the TF-IDF classifier with user corrections.
        This would require retraining the MultinomialNB model with new data.

        Args:
            corrections: List of CorrectionData objects with document details
            model_path: Path to save the updated model (optional, uses self.model_path if not provided)

        Returns:
            bool: True if retraining successful, False otherwise
        """
        try:
            # Use instance model path if not provided
            if model_path is None:
                model_path = self.model_path

            logger.warning(
                f"TF-IDF classifier retraining not yet implemented. "
                f"Would need to retrain with {len(corrections)} corrections. "
                f"This requires access to the original training pipeline."
            )

            # TODO: Implement TF-IDF retraining if needed
            # This would involve:
            # 1. Collecting corrected documents
            # 2. Applying the same cleaning pipeline
            # 3. Retraining MultinomialNB with combined data
            # 4. Saving the updated model and vectorizer

            return False

        except Exception as e:
            logger.error(f"Error in TF-IDF classifier retraining: {e}")
            return False

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the classifier model.
        
        Returns:
            Dict[str, Any]: Dictionary containing model metadata including
            training information, model parameters, performance metrics, etc.
        """
        if not self.classifier_model:
            return {
                "error": "Model not loaded",
                "model_path": self.model_path,
            }
        
        # Use model_dump to get all metadata, excluding None values and training objects
        return self.classifier_model.model_dump(
            mode='json'  # Convert Path objects to strings
        )

    def get_classifier_info(self) -> dict:
        """
        Get comprehensive information about the loaded model for frontend visualization.
        
        Returns:
            Dictionary containing:
            - Basic model info (name, type, class names)
            - Full metadata (file paths, class mappings, training metadata)
        """
        base_info = super().get_classifier_info()
        
        # Add model-specific info
        base_info.update({
            "model_name": self.model_name,
            "class_names": self.class_names,
            "is_initialized": self.is_initialized,
        })
        
        # Note: training_metadata is already included in base_info["metadata"] 
        # from get_metadata() -> classifier_model.model_dump(), so no need to add it again
        
        return base_info

    def get_tokenizer(self) -> TfidfVectorizer:
        """
        Return the vectorizer for the classifier.
        Note: TF-IDF uses a vectorizer, not a tokenizer, but this method
        returns the vectorizer for consistency with the interface.
        """
        return self.vectorizer

    def get_max_sequence_length(self) -> int:
        """
        Get the maximum sequence length for the classifier.
        TF-IDF doesn't have a strict sequence length limit, but we return
        a reasonable default based on typical document sizes.
        """
        # TF-IDF can handle variable-length documents
        # Return a large value to indicate no strict limit
        return 100000  # 100k characters is a reasonable upper bound

    def classify_document(
        self, 
        page_texts: List[Tuple[str, int]], 
        filename: str = None
    ) -> Tuple[str, float, int, Dict[str, Any]]:
        """
        Classify a multi-page document using TF-IDF strategy.
        Aggregates all pages into a single document (matching training approach).
        No chunking needed - TF-IDF handles full documents efficiently.
        
        Args:
            page_texts: List of tuples (text, page_number) for each page
            filename: Optional filename for context
            
        Returns:
            Tuple of (category, confidence, page_number, details_dict)
        """
        if not page_texts:
            logger.warning("No page data to classify")
            return ("other", 0.0, 0, {})
        
        # Aggregate pages into a single document (matching training approach)
        # Training uses max_pages=5 (first 5 pages only), so we limit to match
        # This ensures inference matches the training data distribution
        max_pages_for_classification = 5
        pages_to_use = page_texts[:max_pages_for_classification]
        
        # Training concatenated pages with "\n" separator (see PDFProcessor.extract_text_with_tesseract)
        aggregated_text = "\n".join([text for text, _ in pages_to_use])
        
        if not aggregated_text or not aggregated_text.strip():
            logger.warning("Aggregated text is empty")
            return ("other", 0.0, 0, {})
        
        logger.debug(
            f"[TF-IDF] Aggregating {len(pages_to_use)} of {len(page_texts)} pages "
            f"({len(aggregated_text)} characters) for classification "
            f"(limited to first {max_pages_for_classification} pages to match training)"
        )
        
        try:
            # Classify the full aggregated document (no chunking needed for TF-IDF)
            result = self.classify(aggregated_text, filename)
            
            # Return first page number as reference (since we classified the whole document)
            first_page_num = page_texts[0][1] if page_texts else 0
            
            logger.debug(
                f"[TF-IDF] Full document classification: {result.category} "
                f"(confidence: {result.confidence:.3f})"
            )
            
            return (
                result.category,
                result.confidence,
                first_page_num,
                result.details
            )
        except Exception as e:
            logger.error(f"[TF-IDF] Failed to classify aggregated document: {e}", exc_info=True)
            first_page_num = page_texts[0][1] if page_texts else 0
            return ("other", 0.0, first_page_num, {})

