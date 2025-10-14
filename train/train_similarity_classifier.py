#!/usr/bin/env python3
"""
Training script for similarity-based document classifier.
This script trains the classifier using text files from the document_dataset folder
and saves the trained model for use by the backend inference service.
Uses SentenceTransformer embeddings with cosine similarity for classification.
"""

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimilarityTrainer:
    """Trains a similarity-based document classifier using SentenceTransformer embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.category_embeddings = {}
        self.category_samples = {}

    def initialize(self):
        """Initialize the transformer model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Initialized transformer model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            return False

    def load_training_data(
        self, base_path: str
    ) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """
        Load training data from text files organized by category and split into train/validation.

        Args:
            base_path: Path to the document_dataset folder

        Returns:
            Tuple of (training_data, validation_data) dictionaries mapping categories to lists of text content
        """
        all_data = {}
        base_dir = Path(base_path)

        if not base_dir.exists():
            logger.error(f"Training data directory not found: {base_path}")
            return {}, {}

        # Process each category folder
        for category_dir in base_dir.iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                logger.info(f"Loading data for category: {category_name}")

                texts = []
                for text_file in category_dir.glob("*.txt"):
                    try:
                        with open(text_file, "r", encoding="utf-8") as f:
                            text = f.read().strip()
                            if text:
                                texts.append(text)
                                logger.debug(f"Loaded text from {text_file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to load {text_file}: {e}")

                if texts:
                    all_data[category_name] = texts
                    logger.info(f"Loaded {len(texts)} documents for {category_name}")
                else:
                    logger.warning(f"No valid texts found for {category_name}")

        # Split data into train/validation (80/20)
        training_data = {}
        validation_data = {}

        for category, texts in all_data.items():
            if len(texts) < 2:
                # If we have less than 2 samples, put everything in training
                training_data[category] = texts
                validation_data[category] = []
                logger.warning(
                    f"Category {category} has only {len(texts)} samples, using all for training"
                )
            else:
                # Split 80/20
                train_texts, val_texts = train_test_split(
                    texts, test_size=0.2, random_state=42, shuffle=True
                )
                training_data[category] = train_texts
                validation_data[category] = val_texts
                logger.info(
                    f"Split {category}: {len(train_texts)} training, {len(val_texts)} validation"
                )

        return training_data, validation_data

    def build_category_embeddings(self, training_data: Dict[str, List[str]]):
        """
        Build category embeddings from training data.

        Args:
            training_data: Dictionary mapping categories to lists of text content
        """
        logger.info("Building category embeddings...")

        for category, texts in training_data.items():
            if not texts:
                continue

            logger.info(f"Processing {len(texts)} documents for category: {category}")

            # Encode all texts for this category
            embeddings = self.model.encode(texts)

            # Calculate average embedding for the category
            category_embedding = np.mean(embeddings, axis=0)
            self.category_embeddings[category] = category_embedding

            # Store sample texts for reference
            self.category_samples[category] = texts[:5]  # Keep first 5 samples

            logger.info(f"Built embedding for category: {category}")

    def validate_model(self, validation_data: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Validate the trained model using validation data.

        Args:
            validation_data: Dictionary mapping categories to lists of validation text content

        Returns:
            Dictionary containing validation metrics
        """
        logger.info("Validating model...")

        total_samples = 0
        correct_predictions = 0
        category_metrics = {}

        for true_category, texts in validation_data.items():
            if not texts:
                continue

            category_correct = 0
            category_total = len(texts)

            for text in texts:
                # Classify the text
                text_embedding = self.model.encode([text], convert_to_tensor=False)[0]

                # Calculate similarities with all categories
                similarities = {}
                for category, category_embedding in self.category_embeddings.items():
                    similarity = np.dot(text_embedding, category_embedding) / (
                        np.linalg.norm(text_embedding)
                        * np.linalg.norm(category_embedding)
                    )
                    similarities[category] = float(similarity)

                # Find best category
                if similarities:
                    predicted_category = max(
                        similarities.keys(), key=lambda k: similarities[k]
                    )
                    best_similarity = similarities[predicted_category]

                    # Convert similarity to confidence
                    confidence = 1 / (1 + np.exp(-5 * (best_similarity - 0.5)))

                    # If confidence is very low, classify as "other"
                    if confidence < 0.3:
                        predicted_category = "other"
                else:
                    predicted_category = "other"

                # Check if prediction is correct
                if predicted_category == true_category:
                    category_correct += 1
                    correct_predictions += 1

                total_samples += 1

            # Calculate category accuracy
            category_accuracy = (
                category_correct / category_total if category_total > 0 else 0.0
            )
            category_metrics[true_category] = {
                "accuracy": category_accuracy,
                "correct": category_correct,
                "total": category_total,
            }

            logger.info(
                f"Category {true_category}: {category_correct}/{category_total} correct ({category_accuracy:.3f})"
            )

        # Calculate overall accuracy
        overall_accuracy = (
            correct_predictions / total_samples if total_samples > 0 else 0.0
        )

        validation_metrics = {
            "overall_accuracy": overall_accuracy,
            "total_samples": total_samples,
            "correct_predictions": correct_predictions,
            "category_metrics": category_metrics,
        }

        logger.info(
            f"Overall validation accuracy: {overall_accuracy:.3f} ({correct_predictions}/{total_samples})"
        )

        return validation_metrics

    def save_model(self, output_dir: str, validation_metrics: Dict[str, float] = None):
        """
        Save the trained model and metadata.

        Args:
            output_dir: Directory to save the model files
            validation_metrics: Optional validation metrics to save
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save category embeddings as JSON (portable)
        embeddings_file = output_path / "category_embeddings.json"
        with open(embeddings_file, "w") as f:
            # Convert numpy arrays to lists for JSON serialization
            serializable_embeddings = {
                category: embedding.tolist()
                for category, embedding in self.category_embeddings.items()
            }
            json.dump(serializable_embeddings, f, indent=2)

        # Save model metadata
        metadata = {
            "model_name": self.model_name,
            "categories": list(self.category_embeddings.keys()),
            "category_samples": self.category_samples,
            "embedding_dimension": (
                len(next(iter(self.category_embeddings.values())))
                if self.category_embeddings
                else 0
            ),
        }

        # Add validation metrics if provided
        if validation_metrics:
            metadata["validation_metrics"] = validation_metrics

        metadata_file = output_path / "model_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to {output_dir}")
        logger.info(f"Categories: {list(self.category_embeddings.keys())}")
        logger.info(f"Embedding dimension: {metadata['embedding_dimension']}")

        if validation_metrics:
            logger.info(
                f"Validation accuracy: {validation_metrics['overall_accuracy']:.3f}"
            )

    def train(self, data_path: str, output_dir: str):
        """
        Complete training pipeline with validation.

        Args:
            data_path: Path to the document_dataset folder
            output_dir: Directory to save the trained model
        """
        logger.info("Starting similarity-based classifier training...")

        # Initialize model
        if not self.initialize():
            return False

        # Load and split training data (80/20)
        training_data, validation_data = self.load_training_data(data_path)
        if not training_data:
            logger.error("No training data loaded")
            return False

        # Build category embeddings using training data only
        self.build_category_embeddings(training_data)

        # Validate the model using validation data
        validation_metrics = None
        if any(validation_data.values()):  # Check if we have any validation data
            validation_metrics = self.validate_model(validation_data)
        else:
            logger.warning("No validation data available for evaluation")

        # Save model with validation metrics
        self.save_model(output_dir, validation_metrics)

        logger.info("Training completed successfully!")
        return True


def main():
    """Main training function."""
    # Import config
    import config as train_config

    # Paths
    data_path = str(train_config.DOCUMENT_DATASET_DIR)
    output_dir = str(train_config.CLASSIFIER_MODEL)

    # Create trainer
    trainer = SimilarityTrainer()

    # Train the model
    success = trainer.train(data_path, output_dir)

    if success:
        print("✅ Training completed successfully!")
        print(f"📁 Model saved to: {output_dir}")
        print("🚀 You can now start the backend for inference")
    else:
        print("❌ Training failed!")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
