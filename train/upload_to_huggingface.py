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

# Load environment variables from .env file
load_dotenv()

# Configuration
HF_USERNAME = "bradenacurtis"
FINETUNE_MODEL_NAME = "scanpro-classifier-v1-finetune"

# Load Hugging Face token from environment
HF_TOKEN = os.getenv("SCANPRO_UPLOAD_TOKEN")

# Paths
ROOT_DIR = Path(__file__).parent.parent
SIMILARITY_MODEL_PATH = ROOT_DIR / "APP_DATA" / "ml_models" / "similarity_classifier"
FINETUNE_MODEL_PATH = ROOT_DIR / "train" / "models" / "finetune_classifier"


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
    else:  # finetune
        return f"""---
license: mit
tags:
- document-classification
- bert
- spanish
- legal-documents
- pytorch
---

# {model_name}

A fine-tuned BERT-based document classifier for Spanish legal documents.

## Model Description

This model is based on `dccuchile/bert-base-spanish-wwm-uncased` and fine-tuned specifically for Spanish legal document classification.

## Categories

- **personas**: Personal documents (birth certificates, IDs, etc.)
- **mercantil**: Commercial documents (business registrations, contracts, etc.)
- **inmuebles**: Real estate documents (property deeds, titles, etc.)

## Usage

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load the model
tokenizer = AutoTokenizer.from_pretrained("bradenacurtis/{model_name}")
model = AutoModelForSequenceClassification.from_pretrained("bradenacurtis/{model_name}")

# Classify a document
text = "Your document text here"
inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
with torch.no_grad():
    outputs = model(**inputs)
    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
```

## Training

Fine-tuned on Spanish legal documents using the Hugging Face Transformers library.

## Performance

Achieves high accuracy on Spanish legal document classification tasks.
"""


def upload_finetune_classifier():
    """Upload the fine-tuned classifier to Hugging Face Hub."""
    print(f"Uploading fine-tuned classifier from {FINETUNE_MODEL_PATH}")

    if not FINETUNE_MODEL_PATH.exists():
        print(f"Error: Model path {FINETUNE_MODEL_PATH} does not exist")
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
            folder_path=str(FINETUNE_MODEL_PATH), repo_id=repo_id, repo_type="model"
        )

        # Upload model card
        model_card = create_model_card("finetune", FINETUNE_MODEL_NAME)
        api.upload_file(
            path_or_fileobj=model_card.encode(),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="model",
        )

        print(f"✅ Successfully uploaded fine-tuned classifier to {repo_id}")
        return True

    except Exception as e:
        print(f"❌ Error uploading fine-tuned classifier: {e}")
        return False


def main():
    """Main function to upload models."""
    print("🚀 Starting model upload to Hugging Face Hub...")
    print(f"Username: {HF_USERNAME}")
    print()

    # Check if token is set
    if not HF_TOKEN:
        print("❌ Please set your Hugging Face token in the environment")
        print("Set SCANPRO_UPLOAD_TOKEN environment variable or add it to .env file")
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
    print("1. Set SCANPRO_UPLOAD_TOKEN environment variable or add it to .env file")
    print("2. Run: python train/upload_to_huggingface.py")
    print("3. Your models will be available at:")
    print(f"   - https://huggingface.co/{HF_USERNAME}/{FINETUNE_MODEL_NAME}")


if __name__ == "__main__":
    main()
