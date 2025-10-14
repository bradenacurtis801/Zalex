# ScanPro

A comprehensive document processing and search system that combines OCR, AI-powered document classification, and semantic search capabilities.

## 🚀 Overview

ScanPro is a full-stack application that allows users to upload documents, automatically classify them by type, and perform intelligent semantic searches across their document collection. The system is designed to handle Spanish legal documents including birth certificates, marriage certificates, and property deeds.

## 🔄 System Pipeline

### 1. Training Phase
**Location**: `train/` directory

1. **Data Preparation**: Collect and organize labeled document images in `document_raw/` directory
2. **OCR Processing**: Extract text from document images using Tesseract and save to `document_dataset/`
3. **Model Training**: Train similarity-based classifier using SentenceTransformer embeddings
4. **Model Evaluation**: Test model performance and confidence scores
5. **Model Export**: Save trained models to `APP_DATA/ml_models/classifier_model/` for backend inference

### 2. Backend Processing
**Location**: `backend/` directory

1. **Document Upload**: Receive documents via FastAPI endpoints
2. **OCR Extraction**: Extract text using Tesseract with image preprocessing
3. **Document Classification**: Use pre-trained similarity classifier to classify document types
4. **Embedding Generation**: Create vector embeddings for semantic search
5. **Index Storage**: Store documents in FAISS search index
6. **Search API**: Provide semantic search capabilities

### 3. Frontend Interface
**Location**: `frontend/` directory

1. **Document Upload**: User-friendly interface for file uploads with drag & drop
2. **Category Management**: Browse and view documents organized by classification categories
3. **Document Classification**: Real-time document type classification with confidence scores
4. **Search Interface**: Query interface for semantic search
5. **Results Display**: Show search results with document metadata
6. **Document Management**: View and manage uploaded documents by category

## 🛠️ Getting Started

1. **Train Models**: Use the training pipeline to create document classification models
2. **Start Backend**: Launch the FastAPI server to process documents and provide search
3. **Start Frontend**: Launch the web interface to upload documents and search

See individual component READMEs for detailed setup instructions.

## 🔄 System Flow

### Training Phase
1. **Collect Document Images**: Gather labeled Spanish legal documents in `document_raw/` directory structure
2. **Extract Text**: Use Tesseract OCR to convert document images to text and save to `document_dataset/`
3. **Train Models**: Train similarity-based classifier using SentenceTransformer embeddings
4. **Deploy Models**: Save trained models to `APP_DATA/ml_models/classifier_model/` for backend use

### Backend Processing
1. **Load Models**: Load pre-trained similarity classifier from `APP_DATA/ml_models/classifier_model/`
2. **Receive Documents**: Accept PDF and image uploads via API
3. **Extract Text**: Use Tesseract OCR to extract text from uploaded documents
4. **Classify Documents**: Use pre-trained similarity classifier to determine document type
5. **Create Embeddings**: Generate vector embeddings for semantic search
6. **Store in Index**: Save documents and embeddings in searchable index
7. **Provide Search**: Return relevant documents based on user queries

### Frontend Interface
1. **Upload Documents**: Users upload PDFs and images through web interface
2. **Submit Queries**: Users search for documents using natural language
3. **View Results**: Display search results with document metadata and classification
4. **Manage Documents**: Browse and manage uploaded document collection

## 🚀 Model Deployment Strategy

### Development/Testing
- **Local Models**: Models saved to `APP_DATA/ml_models/classifier_model/` for testing
- **Shared Directory**: Both training and backend use the same `APP_DATA` directory
- **Quick Iteration**: Fast model testing without deployment overhead

### Production Deployment
- **Model URL**: Backend can download models from URLs using `SCANPRO_MODEL_URL`
- **Local Path**: Backend can use local model paths with `SCANPRO_MODEL_PATH`
- **Automatic Discovery**: Backend automatically finds models in `APP_DATA/ml_models/classifier_model/`

### Model Lifecycle
1. **Train**: Create models in training pipeline (`train/train_similarity_classifier.py`)
2. **Save**: Models automatically saved to `APP_DATA/ml_models/classifier_model/`
3. **Load**: Backend automatically loads models from the same directory
4. **Update**: Retrain and save new models to the same location

## 📚 Component Documentation

Each component has its own detailed documentation with setup instructions and code examples:

- **Training Pipeline**: `train/README.md` - Model training, data preparation, and evaluation
- **Backend Server**: `backend/README.md` - API documentation, setup, and deployment
- **Frontend Application**: `frontend/README.md` - User interface development and deployment

## 🎯 Key Technologies

- **Document Classification**: Similarity-based classifier with SentenceTransformer embeddings
- **OCR Processing**: Tesseract for text extraction
- **Search Engine**: FAISS vector search with SentenceTransformer embeddings
- **Backend**: FastAPI for API services
- **Frontend**: Next.js for web interface
- **Training**: Similarity-based classification and SentenceTransformers for model development
