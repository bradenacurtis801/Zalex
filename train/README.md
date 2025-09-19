# ScanPro Training Module

This directory contains all the machine learning training code for ScanPro. It's separate from the main backend to keep the FastAPI server lightweight and focused on serving requests.

## 📁 Structure

```
train/
├── config.py                    # Training configuration and paths
├── requirements.txt             # Training-specific dependencies
├── README.md                    # This file
├── ml/                          # Machine learning modules
│   ├── classification/          # Document classification
│   │   ├── finetune_and_predict.py
│   │   ├── model_config.py
│   │   └── document_classifier.py
│   ├── ner/                     # Named Entity Recognition
│   │   └── named_entity_recognition.py
│   └── preprocessing/           # Image preprocessing (shared with backend)
│       ├── adaptive_pre_processing.py
│       └── tesseract_preprocess.py
└── scripts/                     # Training scripts
    ├── train_spanish_classifier.py
    ├── train_general_classifier.py
    ├── test_spanish_models.py
    ├── setup_models.py
    └── download_models.py
```

## 🚀 Quick Start

1. **Install training dependencies:**
   ```bash
   cd train
   pip install -r requirements.txt
   ```

2. **Train a Spanish document classifier:**
   ```bash
   python main.py train
   # or
   python train.py train
   ```

3. **Test model availability:**
   ```bash
   python main.py test
   # or
   python train.py test
   ```

4. **Setup models:**
   ```bash
   python main.py setup
   # or
   python train.py setup
   ```

## 📊 Available Models

The training module supports several Spanish language models:

- **PlanTL-GOB-ES/roberta-base-bne**: Official Spanish RoBERTa (default)
- **PlanTL-GOB-ES/roberta-large-bne**: Large Spanish RoBERTa
- **BSC-LT/roberta-base-bne-capitel-ner**: Spanish NER model
- **BSC-LT/roberta-base-biomedical-es**: Spanish biomedical model

## 🔧 Configuration

Training paths and settings are configured in `config.py`. The module uses the `scripts/APP_DATA/` directory for:
- Training data (`document_dataset/`)
- Model outputs (`ml_models/`)
- Training logs (`training_logs/`)
- Training results (`training_results/`)

## 📝 Usage

### Training a New Model

```python
from ml.classification.finetune_and_predict import load_and_prepare_data, fine_tune_model

# Load your labeled data
df, id2label, label2id = load_and_prepare_data("path/to/your/data")

# Train the model
fine_tune_model(df, id2label, label2id)
```

### Using a Trained Model

```python
from ml.classification.finetune_and_predict import DocumentClassifier

# Load trained model
classifier = DocumentClassifier("path/to/trained/model")

# Classify a document
predicted_type, confidence = classifier.classify("path/to/document.txt")
print(f"Document type: {predicted_type} (confidence: {confidence:.2%})")
```

## 🔄 Integration with Backend

After training, models are automatically available to the FastAPI backend through the `inference_classifier.py` module, which provides a lightweight interface for document classification without training dependencies.
