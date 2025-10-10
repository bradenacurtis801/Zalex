#!/usr/bin/env python3
"""
Main training entry point for ScanPro document classification models.
This script provides a unified interface for all training operations.
"""

import argparse
import sys
from pathlib import Path

from config import DOCUMENT_DATASET_DIR, SPANISH_CLASSIFIER_MODEL
from ml.classification.finetune_and_predict import (
    DocumentClassifier,
    fine_tune_model,
    load_and_prepare_data,
)


def train_spanish_classifier():
    """Train the Spanish document classifier."""
    print("=== Spanish Document Classifier Training ===")

    # Check if data directory exists
    data_dir = str(DOCUMENT_DATASET_DIR)
    if not Path(DOCUMENT_DATASET_DIR).exists() or not list(
        Path(DOCUMENT_DATASET_DIR).iterdir()
    ):
        print(f"ERROR: Data directory '{data_dir}' is empty or doesn't exist.")
        print("Please ensure you have labeled document folders with .txt files.")
        print("\nExpected structure:")
        print("document_dataset/")
        print("├── birth_certificate/")
        print("│   ├── file1.txt")
        print("│   └── file2.txt")
        print("├── marriage_certificate/")
        print("│   └── file1.txt")
        print("└── property_deeds/")
        print("    └── file1.txt")
        return False

    # Check if model already exists
    if SPANISH_CLASSIFIER_MODEL.exists():
        print(f"Model already exists at {SPANISH_CLASSIFIER_MODEL}")
        response = input("Do you want to retrain? (y/N): ")
        if response.lower() != "y":
            print("Training cancelled.")
            return False

    try:
        # Step 1: Load and prepare data
        print("\n1. Loading and preparing data...")
        df, id2label, label2id = load_and_prepare_data(data_dir)

        # Step 2: Train the model
        print("\n2. Starting model training...")
        fine_tune_model(df, id2label, label2id)

        # Step 3: Test the trained model
        print("\n3. Testing the trained model...")
        classifier = DocumentClassifier(str(SPANISH_CLASSIFIER_MODEL))

        # Test with a sample file if it exists
        test_file = "test_data/es/sample_document_to_classify.txt"
        if Path(test_file).exists():
            predicted_type, confidence = classifier.classify(test_file)
            print(f"Test prediction: {predicted_type} (confidence: {confidence:.2%})")

        print("\n✅ Training completed successfully!")
        print(f"Model saved to: {SPANISH_CLASSIFIER_MODEL}")
        return True

    except Exception as e:
        print(f"❌ Training failed: {e}")
        raise e


def test_models():
    """Test trained model performance."""
    print("=== Testing Trained Model ===")

    try:
        # Import the test script we created
        from tests.test_trained_model import test_trained_model, test_with_custom_text

        print("🧪 Testing trained Spanish document classifier...")
        print("=" * 60)

        # Test with existing documents
        success = test_trained_model()

        if success:
            # Test with custom text
            test_with_custom_text()
            print("\n✅ All tests completed successfully!")
            return True
        else:
            print("\n❌ Model testing failed!")
            return False

    except Exception as e:
        print(f"❌ Model testing failed: {e}")
        return False


def setup_models():
    """Setup and download required models."""
    print("=== Setting Up Models ===")

    try:
        from scripts.setup_models import main as setup_main

        setup_main()
        return True
    except Exception as e:
        print(f"❌ Model setup failed: {e}")
        return False


def main():
    """Main entry point for training operations."""
    # Create all required directories
    print("📁 Creating training directories...")
    from config import (
        APP_DIR,
        DOCUMENT_DATASET_DIR,
        DOCUMENT_RAW_DIR,
        ML_MODELS_DIR,
        TRAINING_LOGS_DIR,
        TRAINING_RESULTS_DIR,
    )

    APP_DIR.mkdir(parents=True, exist_ok=True)
    DOCUMENT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DOCUMENT_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TRAINING_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TRAINING_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    print("✅ Training directories created successfully")

    parser = argparse.ArgumentParser(description="ScanPro Training Pipeline")
    parser.add_argument(
        "command",
        nargs="?",  # Make argument optional
        default="train",  # Set default to "train"
        choices=["train", "test", "setup"],
        help="Command to run: train (train models), test (test models), setup (setup models). Default: train",
    )

    args = parser.parse_args()

    if args.command == "train":
        success = train_spanish_classifier()
        sys.exit(0 if success else 1)
    elif args.command == "test":
        success = test_models()
        sys.exit(0 if success else 1)
    elif args.command == "setup":
        success = setup_models()
        sys.exit(0 if success else 1)


7
if __name__ == "__main__":
    main()
