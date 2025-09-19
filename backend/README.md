# ScanPro Backend

A FastAPI-based document processing and search backend that provides OCR, text extraction, semantic search, document indexing, and document classification capabilities.

## 🚀 Features

- **Document Upload & Processing**: Support for PDF and image files (JPG, PNG, JPEG)
- **OCR Text Extraction**: EasyOCR integration for accurate text recognition
- **Document Classification**: AI-powered document type classification (birth certificates, marriage certificates, property deeds)
- **Semantic Search**: FAISS-based vector search using SentenceTransformer embeddings
- **Document Indexing**: Persistent storage of document metadata and search indices
- **Image Preprocessing**: Advanced image preprocessing for better OCR accuracy
- **RESTful API**: Clean FastAPI endpoints with automatic OpenAPI documentation
- **Comprehensive Logging**: Debug-level logging for troubleshooting and monitoring

## 📁 Project Structure

```
backend/
├── main.py                          # FastAPI application entry point
├── app_state.py                     # Application state management (singleton)
├── config.py                        # Configuration and path management
├── requirements.txt                 # Backend dependencies
├── APP_DATA/                        # Application data directory (development only)
│   ├── uploads/                     # Uploaded files storage
│   ├── document_index.faiss         # FAISS search index
│   ├── document_metadata.json       # Document metadata storage
│   └── ml_models/                   # Pre-trained models
└── src/
    ├── models/                      # Pydantic models for API requests/responses
    │   ├── query.py                 # Query-related models
    │   └── upload.py                # Upload-related models
    ├── routers/                     # FastAPI route handlers
    │   ├── query.py                 # Search/query endpoints
    │   └── upload.py                # File upload endpoints
    ├── services/                    # Business logic services
    │   └── document_processor.py    # Document processing pipeline
    ├── ocr/                         # OCR-related modules
    │   └── ocr_reader.py            # EasyOCR wrapper
    ├── ml/                          # Machine learning modules (inference only)
    │   ├── classification/          # Document classification
    │   │   └── inference_classifier.py # Inference-only classifier
    │   └── preprocessing/           # Image preprocessing
    │       └── adaptive_pre_processing.py
    └── utils/                       # Utility functions
        ├── path_utils.py
        └── viz_tools.py
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- pip or conda

### Setup

1. **Clone and navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables (optional):**
   ```bash
   # For development
   export NODE_ENV=dev
   
   # For production
   export NODE_ENV=production
   ```
   Defaults to dev if env var is not set

## 🚀 Running the Application

### Development Mode

```bash
python main.py
```

The server will start on `http://127.0.0.1:5000`

## 📚 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: `http://127.0.0.1:5000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:5000/redoc`
- **OpenAPI Schema**: `http://127.0.0.1:5000/openapi.json`

## 🔌 API Endpoints

### Upload Endpoints

#### `POST /api/upload`
Upload and process documents for indexing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Array of files (PDF, JPG, PNG, JPEG)

**Response:**
```json
{
  "message": "Enrollment process finished. Successfully indexed 2 file(s)."
}
```

### Query Endpoints

#### `POST /api/query`
Search for documents using semantic similarity.

**Request:**
```json
{
  "query": "What is the main topic of the document?"
}
```

**Response:**
```json
{
  "results": [
    {
      "text": "Extracted text content...",
      "source": "document.pdf",
      "page": 1,
      "score": 0.85
    }
  ]
}
```

## ⚙️ Configuration

The application uses `config.py` for centralized configuration:

### Environment Variables

- `NODE_ENV`: Set to `dev` for development, `production` for production (defaults to `dev`)

### Data Paths

Application data is stored in platform-specific locations:

#### Development Mode (`NODE_ENV=dev`)
All data is stored in the `APP_DATA` directory relative to the backend folder:
- **Uploads**: `APP_DATA/uploads/`
- **Search Index**: `APP_DATA/document_index.faiss`
- **Metadata**: `APP_DATA/document_metadata.json`
- **ML Models**: `APP_DATA/ml_models/`
- **Training Data**: `APP_DATA/training_data/`

#### Production Mode
Data is stored in platform-specific application data directories:

**Windows:**
- **Base Directory**: `%APPDATA%\ScanPro\`
- **Uploads**: `%APPDATA%\ScanPro\uploads\`
- **Search Index**: `%APPDATA%\ScanPro\document_index.faiss`
- **Metadata**: `%APPDATA%\ScanPro\document_metadata.json`

**macOS:**
- **Base Directory**: `~/Library/Application Support/ScanPro/`
- **Uploads**: `~/Library/Application Support/ScanPro/uploads/`
- **Search Index**: `~/Library/Application Support/ScanPro/document_index.faiss`
- **Metadata**: `~/Library/Application Support/ScanPro/document_metadata.json`

**Linux:**
- **Base Directory**: `~/.config/ScanPro/`
- **Uploads**: `~/.config/ScanPro/uploads/`
- **Search Index**: `~/.config/ScanPro/document_index.faiss`
- **Metadata**: `~/.config/ScanPro/document_metadata.json`

## 🧠 Machine Learning Components

### OCR Engine
- **EasyOCR**: Multi-language text recognition
- **Languages**: English and Spanish support
- **Image Preprocessing**: Adaptive preprocessing for better OCR accuracy

### Document Classification
- **Model**: Spanish RoBERTa-based models (PlanTL-GOB-ES)
- **Types**: Birth certificates, marriage certificates, property deeds
- **Confidence Scoring**: Provides confidence levels for predictions
- **Training**: Separate training pipeline in `/train` folder

### Embedding Model
- **SentenceTransformer**: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Use Case**: Semantic similarity search

### Search Engine
- **FAISS**: Facebook AI Similarity Search
- **Index Type**: IndexFlatL2 (L2 distance)
- **Persistence**: Automatic save/load on startup

## 🔧 Development

### Adding New Features

1. **New API Endpoints**: Add to `src/routers/`
2. **New Models**: Add to `src/models/`
3. **New Services**: Add to `src/services/`
4. **New OCR Features**: Add to `src/ocr/`
5. **New ML Features**: Add to `src/ml/` (inference only)

### Model Training

Model training is handled separately in the `../train/` directory. See the main project README for training instructions.

## 📦 Dependencies

See `requirements.txt` for complete list. Key dependencies:

- **FastAPI**: Web framework
- **EasyOCR**: OCR engine
- **FAISS**: Vector search
- **SentenceTransformers**: Embedding model
- **PyMuPDF**: PDF processing
- **Pillow**: Image processing
- **OpenCV**: Image preprocessing
- **Transformers**: Model inference (without training dependencies)