# ScanPro Backend

A FastAPI-based document processing and search backend that provides OCR, text extraction, semantic search, document indexing, and document classification capabilities.

## 🚀 Features

- **User Authentication & Authorization**: Secure login/logout with session management and role-based access control
- **User Management**: Admin interface for creating, editing, and managing user accounts
- **Password Security**: Users can change passwords, admins can reset passwords with session invalidation
- **Document Upload & Processing**: Support for PDF and image files (JPG, PNG, JPEG)
- **OCR Text Extraction**: Tesseract integration for accurate text recognition
- **Document Classification**: Similarity-based document type classification (personas, mercantil, inmuebles)
- **Semantic Search**: FAISS-based vector search using SentenceTransformer embeddings
- **Document Indexing**: Persistent storage of document metadata and search indices
- **Image Preprocessing**: Advanced image preprocessing for better OCR accuracy
- **RESTful API**: Clean FastAPI endpoints with automatic OpenAPI documentation
- **Layered Architecture**: Service layer with dependency injection for maintainable code
- **Centralized Exception Handling**: Global exception mapping with proper HTTP status codes
- **WebSocket Integration**: Real-time progress tracking and notifications
- **Production Ready**: Optimized logging and error handling for production deployment

## 🏗️ Architecture

The backend follows a clean layered architecture pattern:

### **API Layer** (`routers/`)
- Thin FastAPI route handlers
- No business logic, only request/response handling
- Uses dependency injection for service access

### **Service Layer** (`services/`)
- Contains all business logic
- `QueryService`: Handles document search operations
- `UploadService`: Handles file upload and processing

### **Core Layer** (`core/`)
- Centralized exception handling
- Custom exception types with HTTP status mapping
- Global exception handler for consistent error responses

### **Utils Layer** (`utils/`)
- Document processing pipeline
- Utility functions and helpers
- Moved from services for better separation of concerns

### **Dependency Injection** (`dependencies.py`)
- Centralized service instantiation
- Easy testing and mocking
- Clean separation of concerns

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
    ├── core/                        # Core application modules
    │   └── exceptions.py            # Centralized exception handling
    ├── models/                      # Pydantic models for API requests/responses
    │   ├── query.py                 # Query-related models
    │   └── upload.py                # Upload-related models
    ├── routers/                     # FastAPI route handlers (thin API layer)
    │   ├── query.py                 # Search/query endpoints
    │   └── upload.py                # File upload endpoints
    ├── services/                    # Business logic services
    │   ├── query_service.py         # Query/search business logic
    │   └── upload_service.py        # Upload processing business logic
    ├── dependencies.py              # Dependency injection functions
    ├── ocr/                         # OCR-related modules
    │   ├── base.py                  # OCR engine base classes
    │   ├── tesseract_engine.py      # Tesseract OCR implementation
    │   ├── factory.py               # OCR engine factory
    │   └── ocr_reader.py            # Legacy OCR reader interface
    ├── ml/                          # Machine learning modules (inference only)
    │   ├── classification/          # Document classification
    │   │   ├── base_classifier.py   # Base classifier classes
    │   │   ├── pretrained_classifier.py # PreTrainedSimilarityClassifier
    │   │   └── model_loader.py      # Model loading functions
    │   └── preprocessing/           # Image preprocessing
    │       └── adaptive_pre_processing.py
    └── utils/                       # Utility functions
        ├── document_processor.py    # Document processing pipeline
        ├── model_updater.py         # Incremental model update helpers
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

### Authentication Endpoints

#### `POST /api/auth/login`
Authenticate user and create session.

**Request:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "session_token": "abc123...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### `GET /api/auth/me`
Get current user information.

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "Administrator",
  "user_role": "admin",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### `POST /api/auth/change-password`
Change current user's password.

**Request:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

### User Management Endpoints (Admin Only)

#### `GET /api/auth/users`
Get all users (admin only).

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Administrator",
    "user_role": "admin",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### `POST /api/auth/users`
Create new user (admin only).

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "full_name": "New User",
  "password": "password123",
  "user_role": "user"
}
```

#### `PUT /api/auth/users/{user_id}`
Update user (admin only).

**Request:**
```json
{
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "user_role": "admin"
}
```

#### `POST /api/auth/users/{user_id}/reset-password`
Reset user password (admin only).

**Request:**
```json
{
  "new_password": "newpassword123"
}
```

#### `DELETE /api/auth/users/{user_id}`
Delete user (admin only, cannot delete self).

### Upload Endpoints

#### `POST /api/upload`
Upload and process documents for indexing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Array of files (PDF, JPG, PNG, JPEG)

**Response:**
```json
{
  "message": "Successfully processed 2 file(s)."
}
```

**Error Responses:**
- **503 Service Unavailable**: OCR service not available
- **500 Internal Server Error**: Document processing failed
- **400 Bad Request**: Invalid request or file validation error
- **413 Payload Too Large**: File too large

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

### Category Endpoints

#### `GET /api/categories`
Get all available categories and their document counts.

**Response:**
```json
{
  "categories": {
    "personas": [
      {
        "filename": "birth_certificate.pdf",
        "filePath": "/uploads/birth_certificate.pdf",
        "category": "personas",
        "confidence": 0.95,
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ],
    "mercantil": []
  },
  "total_documents": 1
}
```

#### `GET /api/categories/{category}`
Get all documents in a specific category.

**Parameters:**
- `category`: Category name (e.g., "personas", "mercantil", "inmuebles")

**Response:**
```json
{
  "category": "personas",
  "documents": [
    {
      "filename": "birth_certificate.pdf",
      "filePath": "/uploads/birth_certificate.pdf",
      "category": "personas",
      "confidence": 0.95,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 1
}
```

#### `GET /api/categories/summary`
Get a summary of document counts per category.

**Response:**
```json
{
  "personas": 5,
  "mercantil": 3,
  "inmuebles": 2
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
- **Tesseract**: Multi-language text recognition
- **Languages**: English and Spanish support
- **Image Preprocessing**: Adaptive preprocessing for better OCR accuracy

### Document Classification
- **Model**: Similarity-based classifier with SentenceTransformer embeddings
- **Types**: Personas, mercantil, inmuebles (Spanish legal documents)
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
- **Tesseract**: OCR engine
- **FAISS**: Vector search
- **SentenceTransformers**: Embedding model
- **PyMuPDF**: PDF processing
- **Pillow**: Image processing
- **OpenCV**: Image preprocessing
- **Requests**: Model downloading