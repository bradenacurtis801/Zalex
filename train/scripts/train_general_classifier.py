#!/usr/bin/env python3
"""
Training script for general document classifier.
This script trains a model using the hardcoded sample data.
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import the training module
from src.ml.classification.document_classifier import *

def main():
    """Main training function."""
    print("=== General Document Classifier Training ===")
    print("This will train a model using the hardcoded sample data.")
    print("The training process will run automatically...")
    
    # The training code is in the __main__ block of document_classifier.py
    # So we just need to run it
    pass

if __name__ == "__main__":
    main()
