#!/usr/bin/env python3
"""
Training script for Spanish document classifier.
This script trains a model to classify Spanish documents into categories.
"""

import sys
import os
from pathlib import Path

# Add the train directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from ml.classification.finetune_and_predict import (
    load_and_prepare_data, 
    fine_tune_model,
    DocumentClassifier
)
from config import DOCUMENT_DATASET_DIR, SPANISH_CLASSIFIER_MODEL

def main():
    """Main training function."""
    print("=== Spanish Document Classifier Training ===")
    
    # Check if data directory exists
    data_dir = str(DOCUMENT_DATASET_DIR)
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
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
        return
    
    # Check if model already exists
    if os.path.exists(str(SPANISH_CLASSIFIER_MODEL)):
        print(f"Model already exists at {SPANISH_CLASSIFIER_MODEL}")
        response = input("Do you want to retrain? (y/N): ")
        if response.lower() != 'y':
            print("Training cancelled.")
            return
    
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
        test_file = "backend/test_data/es/sample_document_to_classify.txt"
        if os.path.exists(test_file):
            predicted_type, confidence = classifier.classify(test_file)
            print(f"Test prediction: {predicted_type} (confidence: {confidence:.2%})")
        
        print("\n✅ Training completed successfully!")
        print(f"Model saved to: {SPANISH_CLASSIFIER_MODEL}")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
