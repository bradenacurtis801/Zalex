# Document Classifier Documentation

## Overview

The ScanPro document classifier uses a fine-tuned BERT model from Hugging Face Hub to automatically categorize Spanish legal documents. The system loads a pre-trained model (`bradenacurtis/scanpro-classifier-v1-finetune`) that has been specifically fine-tuned for Spanish legal document classification. It's designed to handle various types of legal documents commonly found in Spanish-speaking countries.

## Architecture

### Classification Method
- **Type**: Fine-tuned BERT classification using Hugging Face Transformers
- **Model**: Pre-trained BERT model fine-tuned for Spanish legal documents
- **Algorithm**: Neural network classification with softmax output
- **Training**: Supervised learning on labeled Spanish legal document dataset

### Model Components

1. **BERT Tokenizer**: Converts text into token IDs for the neural network
2. **Fine-tuned BERT Model**: Pre-trained BERT model fine-tuned for classification
3. **Classification Head**: Neural network layer that outputs category probabilities
4. **Softmax Activation**: Converts logits to probability distribution over categories

## Training Data

### Document Categories

The classifier is trained on the following Spanish legal document categories:

| Category | Description | Example Documents |
|----------|-------------|-------------------|
| `personas` | Personal identification documents | Birth certificates, ID cards, passports, marriage certificates |
| `mercantil` | Commercial/business documents | Business licenses, commercial registrations, tax documents |
| `inmuebles` | Property/real estate documents | Property deeds, land titles, real estate contracts |

### Data Sources

- **Training Data**: `test_data/es/document_raw/` directory structure
- **Text Extraction**: OCR-processed documents saved to `test_data/es/document_dataset/`
- **Sample Size**: Variable per category (typically 10-100+ documents per category)

### Data Processing Pipeline

1. **Document Collection**: Gather labeled documents in category-specific directories
2. **OCR Processing**: Extract text using Tesseract OCR engine
3. **Text Preprocessing**: Clean and normalize extracted text
4. **Embedding Generation**: Convert text to 768-dimensional vectors using SentenceTransformer
5. **Category Averaging**: Compute average embedding for each category
6. **Model Serialization**: Save embeddings and metadata to JSON files

## Model Files

### Required Files

The model is automatically downloaded from Hugging Face Hub to:
```
APP_DATA/ml_models/
└── bradenacurtis--scanpro-classifier-v1-finetune/
    ├── config.json              # Model configuration
    ├── model.safetensors        # Model weights
    ├── tokenizer.json           # Tokenizer configuration
    ├── vocab.txt                # Vocabulary file
    ├── tokenizer_config.json    # Tokenizer settings
    └── special_tokens_map.json  # Special tokens mapping
```

### File Formats

#### `config.json`
```json
{
  "model_type": "bert",
  "num_labels": 3,
  "label2id": {
    "personas": 0,
    "mercantil": 1,
    "inmuebles": 2
  },
  "id2label": {
    "0": "personas",
    "1": "mercantil", 
    "2": "inmuebles"
  },
  "hidden_size": 768,
  "num_attention_heads": 12
}
```

## Classification Process

### 1. Document Upload
- User uploads PDF or image file
- System extracts text using OCR (Tesseract)

### 2. Text Preprocessing
- Clean and normalize extracted text
- Truncate if necessary (max ~2000 characters)

### 3. Tokenization
- Convert text to token IDs using BERT tokenizer
- Truncate to maximum sequence length (512 tokens)
- Add special tokens ([CLS], [SEP])

### 4. Neural Network Inference
```python
# Forward pass through BERT model
outputs = model(input_ids, attention_mask)
logits = outputs.logits
probabilities = softmax(logits)
```

### 5. Classification Decision
- Select category with highest probability
- Return confidence score (0.0 to 1.0)

## Performance Characteristics

### Accuracy
- **Expected Accuracy**: 80-95% depending on document quality and OCR accuracy
- **Confidence Thresholds**: 
  - High confidence: >0.8
  - Medium confidence: 0.6-0.8
  - Low confidence: <0.6

### Limitations
- **OCR Dependency**: Classification accuracy depends on OCR text extraction quality
- **Language Specific**: Optimized for Spanish legal documents
- **Document Quality**: Poor image quality affects both OCR and classification
- **Category Coverage**: Only classifies into predefined categories

### Strengths
- **Fast Inference**: Real-time classification without GPU requirements
- **Interpretable**: Cosine similarity scores provide confidence measures
- **Extensible**: Easy to add new categories by retraining
- **Lightweight**: Small model size and memory footprint

## Usage Examples

### Python API
```python
from src.ml.classification.finetune_classifier import PreTrainedFinetuneClassifier

# Load classifier from Hugging Face
classifier = PreTrainedFinetuneClassifier(
    model_name_or_path="bradenacurtis/scanpro-classifier-v1-finetune",
    cache_folder="/path/to/cache"
)

# Classify document
result = classifier.classify("Certificado de nacimiento de Juan Pérez")
print(f"Category: {result.category}")
print(f"Confidence: {result.confidence:.3f}")
```

### REST API
```bash
# Upload document for classification
curl -X POST "http://localhost:5000/api/upload" \
  -F "files=@document.pdf"

# Response includes classification
{
  "message": "Successfully processed 1 file(s).",
  "classifications": [
    {
      "filename": "document.pdf",
      "category": "personas",
      "confidence": 0.85
    }
  ]
}
```

## Training the Model

### Prerequisites
- Python 3.8+
- Required packages: `sentence-transformers`, `numpy`, `json`
- Training data in `test_data/es/document_raw/` structure

### Training Command
```bash
cd train
python train_similarity_classifier.py
```

### Training Process
1. **Data Discovery**: Scan `document_raw/` for category directories
2. **Text Extraction**: Process all documents with OCR
3. **Embedding Generation**: Create vectors for all documents
4. **Category Averaging**: Compute average embeddings per category
5. **Model Serialization**: Save embeddings and metadata

## Model Updates

### Retraining
- Add new documents to appropriate category directories
- Run training script to regenerate embeddings
- Model automatically updates on next backend restart

### Adding Categories
1. Create new directory in `document_raw/`
2. Add sample documents
3. Retrain model
4. Update frontend category handling if needed

## Troubleshooting

### Common Issues

**Low Classification Accuracy**
- Check OCR text extraction quality
- Verify document quality and resolution
- Ensure sufficient training data per category

**Model Loading Errors**
- Verify `model_metadata.json` and `category_embeddings.json` exist
- Check file permissions and paths
- Validate JSON file format

**Memory Issues**
- SentenceTransformer models require ~100MB RAM
- Consider using smaller models for resource-constrained environments

### Debug Information
```python
# Get model information
model_info = classifier.get_model_info()
print(f"Model: {model_info['model_name']}")
print(f"Categories: {model_info['categories']}")
print(f"Available: {model_info['is_available']}")
```

## User Feedback System

The ScanPro classifier includes a feedback system that allows users to correct misclassifications. While the fine-tuned BERT model provides high accuracy, user feedback is still valuable for:

1. **Document Reclassification**: Users can correct misclassified documents
2. **Feedback Logging**: All corrections are logged with metadata for analysis
3. **Model Evaluation**: Track classification accuracy and user satisfaction
4. **Future Improvements**: Feedback data can inform future model training

### API Endpoints

#### Reclassify Document
```http
POST /api/feedback/reclassify
Content-Type: application/json

{
  "filename": "documento.pdf",
  "current_category": "other",
  "new_category": "mercantil",
  "confidence": 0.95,
  "user_comment": "This is a commercial document"
}
```

#### Get Feedback Summary
```http
GET /api/feedback/summary

Response:
{
  "total_corrections": 25,
  "corrections_by_category": {
    "mercantil": 10,
    "inmuebles": 8,
    "other": 7
  },
  "last_updated": "2025-01-14T10:35:00Z"
}
```

### Benefits

- **Quality Assurance**: Track and monitor classification accuracy
- **User Satisfaction**: Allow users to correct misclassifications
- **Data Collection**: Gather feedback for future model improvements
- **Audit Trail**: Maintain records of all corrections

## Future Improvements

### Planned Enhancements
- **Multi-language Support**: Extend to other languages
- **Confidence Calibration**: Improve confidence score accuracy
- **Time-based Retraining**: Retrain based on time intervals
- **Category-specific Thresholds**: Different retraining thresholds per category
- **Ensemble Methods**: Combine multiple classification approaches

### Research Directions
- **Fine-tuned Models**: Train domain-specific SentenceTransformer models
- **Few-shot Learning**: Reduce training data requirements
- **Uncertainty Quantification**: Better confidence estimation
- **Advanced Active Learning**: Smarter correction selection

## References

- [SentenceTransformers Documentation](https://www.sbert.net/)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Spanish Legal Document Processing](https://example.com/spanish-legal-docs)
