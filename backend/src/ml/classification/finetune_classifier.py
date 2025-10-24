"""
Pre-trained fine-tuned classifier for inference.
Uses a fine-tuned BERT model for document classification.
"""

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import torch
from huggingface_hub import snapshot_download
from transformers import AutoModelForSequenceClassification, AutoTokenizer

if TYPE_CHECKING:
    from src.models.schemas.feedback import CorrectionData

from .base_classifier import DocumentClassifier, DocumentClassificationResult

logger = logging.getLogger(__name__)


class PreTrainedFinetuneClassifier(DocumentClassifier):
    """
    Pre-trained fine-tuned classifier for inference only.
    Loads a fine-tuned BERT model and provides classification functionality.
    """

    def __init__(
        self,
        model_name_or_path: str,
        cache_folder: Optional[str] = None,
        token: Union[bool, str, None] = None,
    ):
        super().__init__(model_name_or_path, cache_folder, token)
        self.model: Optional[AutoModelForSequenceClassification] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.label2id: Dict[str, int] = {}
        self.id2label: Dict[int, str] = {}
        self.model_name: str = ""

        if cache_folder is None:
            cache_folder = os.getenv('SENTENCE_TRANSFORMERS_HOME')
            if cache_folder is None:
                try:
                    from torch.hub import _get_torch_home

                    torch_cache_home = _get_torch_home()
                except ImportError:
                    torch_cache_home = os.path.expanduser(os.getenv('TORCH_HOME', os.path.join(os.getenv('XDG_CACHE_HOME', '~/.cache'), 'torch')))

                cache_folder = os.path.join(torch_cache_home, 'sentence_transformers')

        self.cache_folder = cache_folder

        # Handle Hugging Face model ID or local path and load the model
        if "/" in model_name_or_path and not os.path.exists(model_name_or_path):

            model_path = str(self.cache_folder / model_name_or_path.replace("/", "-"))
            
            # Check cache for model
            logger.debug(f"Checking cache for model: {model_path}")
            if os.path.exists(model_path) and self.validate_model_directory(model_path):
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
        logger.info("Loading fine-tuned classifier model...")
        self._load_model()

    def _load_model(self) -> None:
        """
        Internal method to load the model during construction.
        Sets is_initialized to True on success, False on failure.
        """
        try:
            model_path = Path(self.model_path)

            # Validate model directory
            if not self.validate_model_directory(self.model_path):
                from ...core.exceptions import InvalidModelDirectoryError

                raise InvalidModelDirectoryError(
                    f"Invalid fine-tuned classifier model directory: {self.model_path}. "
                    f"Required files: config.json, model.safetensors, tokenizer.json, vocab.txt, "
                    f"tokenizer_config.json, special_tokens_map.json"
                )

            # Load model configuration (primary source)
            config_file = model_path / "config.json"
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Validate required config fields
            required_fields = ["label2id", "id2label"]
            missing_fields = [
                field for field in required_fields if field not in config_data
            ]
            if missing_fields:
                from ...core.exceptions import InvalidModelMetadataError

                raise InvalidModelMetadataError(
                    f"Missing required fields in config.json: {missing_fields}. "
                    f"Required fields: {required_fields}"
                )

            # Validate label mappings
            label2id = config_data.get("label2id", {})
            id2label = config_data.get("id2label", {})

            if not isinstance(label2id, dict) or not label2id:
                from ...core.exceptions import InvalidModelMetadataError

                raise InvalidModelMetadataError(
                    f"Invalid 'label2id' field in config.json. Expected non-empty dictionary, got: {type(label2id)}"
                )

            if not isinstance(id2label, dict) or not id2label:
                from ...core.exceptions import InvalidModelMetadataError

                raise InvalidModelMetadataError(
                    f"Invalid 'id2label' field in config.json. Expected non-empty dictionary, got: {type(id2label)}"
                )

            # Validate that label mappings are consistent
            try:
                id2label_converted = {int(k): v for k, v in id2label.items()}
            except (ValueError, TypeError) as e:
                from ...core.exceptions import InvalidModelMetadataError

                raise InvalidModelMetadataError(
                    f"Invalid 'id2label' format in config.json. All keys must be convertible to integers: {e}"
                )

            self.model_name = config_data.get("_name_or_path", "unknown")
            self.label2id = label2id
            self.id2label = id2label_converted

            # Try to load additional metadata if available
            metadata_file = model_path / "model_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    # Use model_name from metadata if available
                    if "model_name" in metadata:
                        self.model_name = metadata["model_name"]

            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                num_labels=len(self.label2id),
                id2label=self.id2label,
                label2id=self.label2id,
            )

            # Set model to evaluation mode
            self.model.eval()

            self.is_initialized = True
            logger.info(f"Successfully loaded fine-tuned model: {self.model_name}")
            logger.info(f"Categories: {list(self.label2id.keys())}")

        except Exception as e:
            logger.error(f"Failed to load fine-tuned model: {e}")
            self.is_initialized = False

    def _download_from_huggingface(
        self, repo_id: str, local_path: str, token: Optional[str] = None
    ) -> str:
        """
        Download model from Hugging Face Hub with caching.

        Args:
            repo_id: Hugging Face repository ID
            local_path: Local path where model should be downloaded
            token: Hugging Face token for private models

        Returns:
            Local path to downloaded model
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

    @staticmethod
    def validate_model_directory(model_path: str) -> bool:
        """
        Validate that a model directory contains all required files for fine-tuned classifier.

        Args:
            model_path: Path to the model directory

        Returns:
            bool: True if valid, False otherwise
        """
        model_dir = Path(model_path)

        if not model_dir.exists():
            return False

        required_files = [
            "config.json",
            "model.safetensors",  # or pytorch_model.bin
            "tokenizer.json",
            "vocab.txt",
            "tokenizer_config.json",
            "special_tokens_map.json",
        ]

        for file_name in required_files:
            if not (model_dir / file_name).exists():
                return False

        return True

    def load_model(self) -> bool:
        """
        Load a pre-trained fine-tuned model from disk.
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
        return list(self.label2id.keys())

    def classify(self, text: str, filename: str = None) -> DocumentClassificationResult:
        """
        Classify text using the fine-tuned model.

        Args:
            text: Input text to classify
            filename: Optional filename for context

        Returns:
            DocumentClassificationResult: Classification result
        """
        if not self.is_initialized or self.model is None or self.tokenizer is None:
            return DocumentClassificationResult(
                category="unknown",
                confidence=0.0,
                method="finetune",
                details={"error": "Classifier not initialized"},
            )

        try:
            # Tokenize input text
            inputs = self.tokenizer(
                text, truncation=True, padding=True, max_length=512, return_tensors="pt"
            )

            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)

            # Get predicted category and confidence
            predicted_id = torch.argmax(logits, dim=-1).item()
            predicted_category = self.id2label.get(predicted_id, "unknown")
            confidence = probabilities[0][predicted_id].item()

            # Get all category probabilities for details
            category_probabilities = {}
            for category, category_id in self.label2id.items():
                category_probabilities[category] = probabilities[0][category_id].item()

            return DocumentClassificationResult(
                category=predicted_category,
                confidence=confidence,
                method="finetune",
                details={
                    "category_probabilities": category_probabilities,
                    "model_name": self.model_name,
                    "filename": filename,
                    "predicted_id": predicted_id,
                },
            )

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return DocumentClassificationResult(
                category="unknown",
                confidence=0.0,
                method="finetune",
                details={"error": str(e)},
            )

    def get_available_categories(self) -> list:
        """Get list of available categories (alias for get_supported_categories)."""
        return self.get_supported_categories()

    def retrain_with_corrections(
        self, corrections: List["CorrectionData"], model_path: Optional[str] = None
    ) -> bool:
        """
        Retrain the fine-tuned classifier with user corrections.
        For fine-tuned models, this would require full retraining which is expensive.
        For now, we'll log a warning and return False.

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
                f"Fine-tuned classifier retraining not yet implemented. "
                f"Would need to retrain with {len(corrections)} corrections. "
                f"This is computationally expensive and a solution has not been implemented yet."
            )

            # TODO: Implement fine-tuned retraining if needed
            # This would involve:
            # 1. Collecting corrected documents
            # 2. Creating new training dataset
            # 3. Fine-tuning the model again
            # 4. Saving the updated model to model_path

            return False

        except Exception as e:
            logger.error(f"Error in fine-tuned classifier retraining: {e}")
            return False

    def get_classifier_info(self) -> dict:
        """Get information about the loaded model."""
        base_info = super().get_classifier_info()
        base_info.update({
            "model_name": self.model_name,
            "label2id": self.label2id,
            "id2label": self.id2label,
        })
        return base_info
