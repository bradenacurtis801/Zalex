#!/usr/bin/env python3
"""
Training script for fine-tuned document classifier.
This script trains a fine-tuned BERT-based classifier using text files from the document_dataset folder
and saves the trained model for use by the backend inference service.
Uses a pre-trained Spanish BERT model fine-tuned on document classification.
"""

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

CLASSIFIER_MODEL_ID = "finetune_classifier"
CLASSIFIER_MODEL_PATH = config.ML_MODELS_DIR / CLASSIFIER_MODEL_ID


class FinetuneTrainer:
    """Trains a fine-tuned BERT-based document classifier."""

    def __init__(self, model_name: str = "dccuchile/bert-base-spanish-wwm-uncased"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.label2id = {}
        self.id2label = {}
        self.num_labels = 0

    def initialize(self):
        """Initialize the tokenizer and model."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logger.info(f"Initialized tokenizer: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize tokenizer: {e}")
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

        # Create label mappings
        categories = sorted(all_data.keys())
        self.label2id = {label: idx for idx, label in enumerate(categories)}
        self.id2label = {idx: label for label, idx in self.label2id.items()}
        self.num_labels = len(categories)

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
                from sklearn.model_selection import train_test_split

                train_texts, val_texts = train_test_split(
                    texts, test_size=0.2, random_state=42, shuffle=True
                )
                training_data[category] = train_texts
                validation_data[category] = val_texts
                logger.info(
                    f"Split {category}: {len(train_texts)} training, {len(val_texts)} validation"
                )

        return training_data, validation_data

    def prepare_dataset(self, data: Dict[str, List[str]]) -> Dataset:
        """Convert data dictionary to HuggingFace Dataset format."""
        texts = []
        labels = []

        for category, category_texts in data.items():
            for text in category_texts:
                texts.append(text)
                labels.append(self.label2id[category])

        # Tokenize texts
        tokenized = self.tokenizer(
            texts, truncation=True, padding=True, max_length=512, return_tensors="pt"
        )

        # Create dataset
        dataset = Dataset.from_dict(
            {
                "input_ids": tokenized["input_ids"],
                "attention_mask": tokenized["attention_mask"],
                "labels": labels,
            }
        )

        return dataset

    def compute_metrics(self, eval_pred):
        """Compute metrics for evaluation."""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)

        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average="weighted"
        )
        accuracy = accuracy_score(labels, predictions)

        return {
            "accuracy": accuracy,
            "f1": f1,
            "precision": precision,
            "recall": recall,
        }

    def train(self, data_path: str, output_dir: str):
        """
        Complete training pipeline with validation.

        Args:
            data_path: Path to the document_dataset folder
            output_dir: Directory to save the trained model
        """
        logger.info("Starting fine-tuned classifier training...")

        # Initialize tokenizer
        if not self.initialize():
            return False

        # Load and split training data (80/20)
        training_data, validation_data = self.load_training_data(data_path)
        if not training_data:
            logger.error("No training data loaded")
            return False

        logger.info(f"Found {self.num_labels} categories: {list(self.label2id.keys())}")

        # Prepare datasets
        train_dataset = self.prepare_dataset(training_data)
        val_dataset = (
            self.prepare_dataset(validation_data)
            if any(validation_data.values())
            else None
        )

        # Initialize model
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=self.num_labels,
            id2label=self.id2label,
            label2id=self.label2id,
        )

        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=10,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=10,
            evaluation_strategy="epoch" if val_dataset else "no",
            save_strategy="epoch",
            save_total_limit=2,
            load_best_model_at_end=True if val_dataset else False,
            metric_for_best_model="f1" if val_dataset else None,
            greater_is_better=True,
            seed=42,
        )

        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self.compute_metrics if val_dataset else None,
            callbacks=(
                [EarlyStoppingCallback(early_stopping_patience=3)]
                if val_dataset
                else None
            ),
        )

        # Train the model
        logger.info("Starting training...")
        trainer.train()

        # Save the model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)

        # Save metadata
        metadata = {
            "model_name": self.model_name,
            "categories": list(self.label2id.keys()),
            "label2id": self.label2id,
            "id2label": self.id2label,
            "num_labels": self.num_labels,
        }

        metadata_file = Path(output_dir) / "model_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to {output_dir}")
        logger.info(f"Categories: {list(self.label2id.keys())}")
        logger.info(f"Number of labels: {self.num_labels}")

        # Final evaluation if validation data available
        if val_dataset:
            logger.info("Running final evaluation...")
            eval_results = trainer.evaluate()
            logger.info(f"Final evaluation results: {eval_results}")

        logger.info("Training completed successfully!")
        return True


def main():
    """Main training function."""
    # Import config
    import config as train_config

    data_path = str(train_config.DOCUMENT_DATASET_DIR)

    # Create trainer
    trainer = FinetuneTrainer()

    # Train the model
    success = trainer.train(data_path, CLASSIFIER_MODEL_PATH)

    if success:
        print("✅ Fine-tuned classifier training completed successfully!")
        print(f"📁 Model saved to: {CLASSIFIER_MODEL_PATH}")
        print("🚀 You can now use this model for inference")
    else:
        print("❌ Training failed!")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
