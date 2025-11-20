# Training Module

This directory contains all the machine learning training code. It's separate from the main backend to keep the FastAPI server lightweight and focused on serving requests.

## 📁 Structure

```
train/
├── config.py                    # Training configuration and paths
├── requirements.txt             # Training-specific dependencies
├── README.md                    # This file
 ├── train_similarity_classifier.py   # Main similarity classifier training script
├── extract_text_from_documents.py # Text extraction from raw documents
├── package_model.py             # Model packaging for distribution
└── APP_DATA/                    # Shared data directory
    ├── document_raw/            # Raw document images organized by category
    ├── document_dataset/        # Processed text files organized by category
    ├── ml_models/               # Trained models
    │   └── classifier_model/    # Default classifier model
    ├── training_results/        # Training outputs
    └── training_logs/           # Training logs
```

## 🚀 Quick Start

1. **Install training dependencies:**
   ```bash
   cd train
   pip install -r requirements.txt
   ```

2. **Extract text from raw documents:**
   ```bash
   python extract_text_from_documents.py
   ```

3. **Train a similarity document classifier:**
   ```bash
   python train_similarity_classifier.py
   ```

4. **Package model for distribution:**
   ```bash
   python package_model.py
   ```

## 📊 Available Models

The training module uses similarity-based classification with SentenceTransformer embeddings:

- **all-MiniLM-L6-v2**: Default SentenceTransformer model for embeddings
- **Cosine Similarity**: Cosine similarity-based classification
- **Dynamic Categories**: Categories discovered from `document_raw/` directory structure

## 🔧 Configuration

Training paths and settings are configured in `config.py`. The module uses the `APP_DATA/` directory for:
- Raw documents (`document_raw/`) - organized by category folders
- Processed text (`document_dataset/`) - extracted text organized by category
- Model outputs (`ml_models/classifier_model/`) - trained similarity classifier
- Training logs (`training_logs/`)
- Training results (`training_results/`)

## 📝 Usage

### Training a New Model

1. **Organize your documents** in `APP_DATA/document_raw/` by category:
   ```
   APP_DATA/document_raw/
   ├── personas/
   ├── mercantil/
   └── inmuebles/
   ```

2. **Extract text** from raw documents:
   ```bash
   python extract_text_from_documents.py
   ```

3. **Train the similarity classifier**:
   ```bash
   python train_similarity_classifier.py
   ```

### Using a Trained Model

The trained model is automatically available to the backend from `APP_DATA/ml_models/classifier_model/`. The backend will load it automatically when starting up.

## 🔄 Integration with Backend

After training, models are automatically available to the FastAPI backend through the `pretrained_classifier.py` module, which provides a lightweight interface for document classification without training dependencies. The backend automatically loads the model from `APP_DATA/ml_models/classifier_model/`.
