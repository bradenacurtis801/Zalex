#!/usr/bin/env python3
"""
Test script to check if Spanish models are available on Hugging Face.
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.ml.classification.model_config import list_available_models, get_model_config
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def test_model_availability():
    """Test if the Spanish models are available."""
    print("Testing Spanish Model Availability")
    print("=" * 50)
    
    models_to_test = [
        "roberta-base-bne",
        "roberta-large-bne", 
        "roberta-ner",
        "roberta-biomedical"
    ]
    
    for model_key in models_to_test:
        try:
            config = get_model_config(model_key)
            model_name = config["name"]
            
            print(f"\nTesting {model_key}: {model_name}")
            print("-" * 40)
            
            # Test tokenizer
            print("  Loading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            print(f"  ✅ Tokenizer loaded successfully")
            
            # Test model
            print("  Loading model...")
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name, 
                num_labels=3  # For our 3 document types
            )
            print(f"  ✅ Model loaded successfully")
            print(f"  📊 Model size: {config['memory_usage']}")
            print(f"  ⚡ Speed: {config['speed']}")
            
        except Exception as e:
            print(f"  ❌ Failed to load {model_key}: {e}")
    
    print("\n" + "=" * 50)
    print("Model availability test complete!")

if __name__ == "__main__":
    list_available_models()
    print("\n")
    test_model_availability()
