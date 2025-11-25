#!/usr/bin/env python3
"""
Upload trained models to Hugging Face Hub.

This script uploads both the similarity classifier and fine-tuned classifier
to Hugging Face Hub for easy distribution and deployment.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi, Repository
from huggingface_hub.utils import RepositoryNotFoundError
import lib.constants as c

# Load environment variables from .env file
load_dotenv()

# Configuration
HF_USERNAME = "bradenacurtis"
FINETUNE_MODEL_NAME = "tfid-classifier"  # Hugging Face repo name
MODEL_DIR_NAME = "bradenacurtis-tfid-classifier"  # Actual directory name in ml_models

# Load Hugging Face token from environment
HF_TOKEN = os.getenv("HF_UPLOAD_TOKEN")

# Paths
ROOT_DIR = Path(__file__).parent.parent
TFIDF_MODEL_PATH = c.ML_MODELS_DIR / MODEL_DIR_NAME


def create_model_card(model_type: str, model_name: str) -> str:
    """Create a model card for the Hugging Face repository."""
    if model_type == "similarity":
        return f"""---
license: mit
tags:
- document-classification
- similarity-search
- spanish
- legal-documents
---

# {model_name}

A similarity-based document classifier trained on Spanish legal documents.

## Model Description

This model uses SentenceTransformer embeddings and cosine similarity to classify Spanish legal documents into categories:
- **personas**: Personal documents (birth certificates, IDs, etc.)
- **mercantil**: Commercial documents (business registrations, contracts, etc.)
- **inmuebles**: Real estate documents (property deeds, titles, etc.)

## Usage

```python
from sentence_transformers import SentenceTransformer
import json

# Load the model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load category embeddings
with open("category_embeddings.json", "r") as f:
    category_embeddings = json.load(f)

# Classify a document
text = "Your document text here"
embedding = model.encode([text])
# ... classification logic
```

## Training Data

Trained on Spanish legal documents from various sources, processed using OCR and structured into categories based on document type.

## Performance

The model achieves high accuracy on Spanish legal document classification tasks.
"""
    else:  # tfidf
        return f"""---
license: mit
tags:
- document-classification
- tfidf
- naive-bayes
- spanish
- legal-documents
- scikit-learn
---

# {model_name}

A TFIDF + Naive Bayes document classifier for Spanish legal documents.

## Model Description

This model uses TFIDF (Term Frequency-Inverse Document Frequency) vectorization combined with a Naive Bayes classifier to classify Spanish legal documents into categories.

## Categories

- **personas**: Personal documents (birth certificates, IDs, etc.)
- **mercantil**: Commercial documents (business registrations, contracts, etc.)
- **inmuebles**: Real estate documents (property deeds, titles, etc.)

## Usage

```python
from lib.models.classifier import TFIDFClassifierModel

# Load the model
model = TFIDFClassifierModel.from_pretrained("bradenacurtis/{model_name}")

# Classify a document
text = "Your document text here"
prediction = model.predict(text)
print(f"Category: {{prediction['category']}}, Confidence: {{prediction['confidence']}}")
```

## Training

Trained on Spanish legal documents using scikit-learn's TFIDF vectorizer and Multinomial Naive Bayes classifier.

## Performance

Achieves high accuracy on Spanish legal document classification tasks with fast inference times.
"""


def upload_finetune_classifier():
    """Upload the TFIDF classifier to Hugging Face Hub."""
    print(f"Uploading TFIDF classifier from {TFIDF_MODEL_PATH}")

    if not TFIDF_MODEL_PATH.exists():
        print(f"Error: Model path {TFIDF_MODEL_PATH} does not exist")
        return False

    try:
        # Create repository with authentication
        api = HfApi(token=HF_TOKEN)
        repo_id = f"{HF_USERNAME}/{FINETUNE_MODEL_NAME}"

        # Create the repository
        try:
            api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
            print(f"Created repository: {repo_id}")
        except Exception as e:
            print(f"Repository might already exist: {e}")

        # Upload files
        api.upload_folder(
            folder_path=str(TFIDF_MODEL_PATH), repo_id=repo_id, repo_type="model"
        )

        # Upload model card
        model_card = create_model_card("tfidf", FINETUNE_MODEL_NAME)
        api.upload_file(
            path_or_fileobj=model_card.encode(),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="model",
        )

        print(f"✅ Successfully uploaded TFIDF classifier to {repo_id}")
        return True

    except Exception as e:
        print(f"❌ Error uploading TFIDF classifier: {e}")
        return False


def main():
    """Main function to upload models."""
    print("🚀 Starting model upload to Hugging Face Hub...")
    print(f"Username: {HF_USERNAME}")
    print()

    # Check if token is set
    if not HF_TOKEN:
        print("❌ Please set your Hugging Face token in the environment")
        print("Set HF_UPLOAD_TOKEN environment variable or add it to .env file")
        print("Get your token from: https://huggingface.co/settings/tokens")
        return

    # Upload models
    finetune_success = upload_finetune_classifier()

    print("\n" + "=" * 50)
    if finetune_success:
        print("🎉 All models uploaded successfully!")
    else:
        print("⚠️  Some uploads failed. Check the errors above.")

    print("\nNext steps:")
    print("1. Set HF_UPLOAD_TOKEN environment variable or add it to .env file")
    print("2. Run: python train/upload_to_huggingface.py")
    print("3. Your models will be available at:")
    print(f"   - https://huggingface.co/{HF_USERNAME}/{FINETUNE_MODEL_NAME}")


if __name__ == "__main__":
    main()
