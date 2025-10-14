# Document Classifier Documentation

## Overview

The ScanPro document classifier is a similarity-based classification system that automatically categorizes Spanish legal documents using SentenceTransformer embeddings and cosine similarity. It's designed to handle various types of legal documents commonly found in Spanish-speaking countries.

## Architecture

### Classification Method
- **Type**: Similarity-based classification using cosine similarity
- **Model**: SentenceTransformer embeddings (768-dimensional vectors)
- **Algorithm**: Cosine similarity between document and category embeddings
- **Training**: Unsupervised learning on document text content

### Model Components

1. **SentenceTransformer Model**: Converts text into 768-dimensional vectors
2. **Category Embeddings**: Pre-computed average embeddings for each document category
3. **Similarity Calculator**: Computes cosine similarity between document and category vectors
4. **Classification Logic**: Assigns document to category with highest similarity score

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

```
APP_DATA/ml_models/classifier_model/
├── model_metadata.json          # Model configuration and metadata
└── category_embeddings.json     # 768-dimensional embeddings for each category
```

### File Formats

#### `model_metadata.json`
```json
{
  "model_name": "all-MiniLM-L6-v2",
  "categories": ["personas", "mercantil", "inmuebles"],
  "embedding_dimension": 768,
  "training_date": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### `category_embeddings.json`
```json
{
  "personas": [0.1, -0.3, 0.7, ...],     // 768 numbers
  "mercantil": [0.2, -0.1, 0.8, ...],    // 768 numbers
  "inmuebles": [0.3, -0.2, 0.6, ...]     // 768 numbers
}
```

## Classification Process

### 1. Document Upload
- User uploads PDF or image file
- System extracts text using OCR (Tesseract)

### 2. Text Preprocessing
- Clean and normalize extracted text
- Truncate if necessary (max ~2000 characters)

### 3. Embedding Generation
- Convert text to 768-dimensional vector using SentenceTransformer
- Use same model as training: `all-MiniLM-L6-v2`

### 4. Similarity Calculation
```python
# For each category
similarity = cosine_similarity(document_vector, category_embedding)
```

### 5. Classification Decision
- Select category with highest similarity score
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
from src.ml.classification.model_loader import load_pretrained_classifier

# Load classifier
classifier = load_pretrained_classifier("/path/to/model")

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

## User Feedback and Model Retraining

The ScanPro classifier includes a sophisticated feedback system that allows users to correct misclassifications and automatically retrain the model based on accumulated feedback.

### Feedback System Overview

The feedback system enables continuous model improvement through user corrections:

1. **Document Reclassification**: Users can correct misclassified documents
2. **Feedback Logging**: All corrections are logged with metadata
3. **Automatic Retraining**: Model updates based on accumulated feedback
4. **Manual Triggers**: Administrators can force model updates

### How It Works

#### 1. User Correction Process

When a user identifies a misclassified document:

```python
# User corrects a document classification
reclassification_request = {
    "filename": "documento.pdf",
    "current_category": "other",
    "new_category": "mercantil", 
    "confidence": 0.95,
    "user_comment": "This is clearly a commercial document"
}
```

The system:
- Updates the document's category in metadata
- Logs the correction with timestamp and user details
- Tracks correction statistics by category
- Determines if model retraining is needed

#### 2. Automatic Model Retraining

The system automatically retrains the model when:

- **Correction Threshold**: Every 10 user corrections
- **Batch Processing**: Processes all corrections since last update
- **Embedding Updates**: Recalculates category embeddings with new data
- **Smart Cleanup**: After retraining, removes only the corrections that were processed, keeping unprocessed ones

```python
def _should_update_model(self) -> bool:
    correction_count = len(self.feedback_data["corrections"])
    
    # Retrain every 10 corrections
    if correction_count % 10 == 0 and correction_count > 0:
        return self._update_model_embeddings()
    
    return False

# After retraining, remove only the processed corrections
corrections_to_remove = len(recent_corrections)
self.feedback_data["corrections"] = self.feedback_data["corrections"][corrections_to_remove:]
```

#### 3. Manual Model Updates

Administrators can trigger immediate model updates:

```bash
# Manual model update via API
curl -X POST http://localhost:8000/api/feedback/update-model
```

### Feedback Data Structure

The system maintains detailed feedback logs:

```json
{
  "corrections": [
    {
      "filename": "documento.pdf",
      "from_category": "other",
      "to_category": "mercantil",
      "confidence": 0.95,
      "user_comment": "Commercial document",
      "timestamp": "2025-01-14T10:30:00Z"
    }
  ],
  "corrections_by_category": {
    "mercantil": 5,
    "inmuebles": 3,
    "other": 2
  },
  "model_updates": [
    {
      "timestamp": "2025-01-14T10:35:00Z",
      "corrections_processed": 10,
      "total_corrections": 10
    }
  ],
  "last_updated": "2025-01-14T10:35:00Z",
  "version": "1.0.0"
}
```

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
  "last_updated": "2025-01-14T10:35:00Z",
  "model_version": "1.0.0"
}
```

#### Trigger Model Update
```http
POST /api/feedback/update-model

Response:
{
  "success": true,
  "message": "Model updated successfully",
  "corrections_processed": 10
}
```

### Model Update Process

When model updating is triggered:

1. **Data Collection**: Gathers all corrections since last update
2. **Text Extraction**: Re-extracts text from corrected documents using existing OCR pipeline
3. **Embedding Generation**: Creates new embeddings for corrected documents using SentenceTransformer
4. **Incremental Update**: Updates category embeddings using weighted averages (70% existing, 30% new)
5. **Model Persistence**: Saves updated embeddings to disk with backup creation
6. **Cleanup**: Removes processed corrections to prevent reprocessing
7. **Logging**: Records update statistics and performance metrics

### Benefits

- **Incremental Learning**: Fast updates without full retraining from scratch
- **Continuous Improvement**: Model accuracy improves over time
- **User-Driven**: Corrections based on real user needs
- **Automated**: No manual intervention required
- **Efficient**: Only processes corrected documents, not entire training dataset
- **Safe**: Creates backups and uses weighted averages to preserve existing knowledge
- **Trackable**: Full audit trail of all changes
- **Scalable**: Handles large volumes of corrections

### Technical Implementation

The incremental model update system uses helper functions in `backend/src/utils/model_updater.py`:

- **`load_existing_embeddings()`**: Loads current category embeddings from disk
- **`extract_corrected_documents()`**: Extracts text from corrected documents using category metadata
- **`generate_embeddings_for_documents()`**: Creates new embeddings using SentenceTransformer
- **`recalculate_category_embeddings()`**: Updates embeddings using weighted averages
- **`save_updated_embeddings()`**: Saves updates with backup creation

### Configuration

The model update system can be configured:

```python
# Update thresholds
CORRECTION_THRESHOLD = 10  # Update every N corrections
WEIGHT_EXISTING = 0.7      # Weight for existing embeddings
WEIGHT_NEW = 0.3           # Weight for new corrections
MAX_BATCH_SIZE = 100       # Maximum corrections per batch
```

### Monitoring

Track model performance and feedback:

- **Correction Rate**: Frequency of user corrections
- **Category Accuracy**: Per-category correction patterns
- **Model Updates**: Retraining frequency and success
- **User Satisfaction**: Feedback quality and consistency

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
