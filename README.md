# ScanPro

A comprehensive document processing and search system that combines OCR, AI-powered document classification, and semantic search capabilities.

## 🚀 Overview

ScanPro is a full-stack application that allows users to upload documents, automatically classify them by type, and perform intelligent semantic searches across their document collection. The system is designed to handle Spanish legal documents including birth certificates, marriage certificates, and property deeds.

## 🔄 System Pipeline

### 1. Training Phase

1. **Data Preparation**: Collect and organize labeled document images
2. **OCR Processing**: Extract text from document images using Tesseract
3. **Model Training**: Fine-tune Spanish RoBERTa models on document classification
4. **Model Evaluation**: Test model performance and confidence scores
5. **Model Export**: Save trained models for backend inference

### 2. Backend Processing

1. **Document Upload**: Receive documents via FastAPI endpoints
2. **OCR Extraction**: Extract text using EasyOCR with image preprocessing
3. **Document Classification**: Use trained models to classify document types
4. **Embedding Generation**: Create vector embeddings for semantic search
5. **Index Storage**: Store documents in FAISS search index
6. **Search API**: Provide semantic search capabilities

### 3. Frontend Interface

1. **Document Upload**: User-friendly interface for file uploads
2. **Search Interface**: Query interface for semantic search
3. **Results Display**: Show search results with document metadata
4. **Document Management**: View and manage uploaded documents

## 🛠️ Getting Started

1. **Train Models**: Use the training pipeline to create document classification models
2. **Start Backend**: Launch the FastAPI server to process documents and provide search
3. **Start Frontend**: Launch the web interface to upload documents and search

See individual component READMEs for detailed setup instructions.

## 🔄 System Flow

### Training Phase
1. **Collect Document Images**: Gather labeled Spanish legal documents (birth certificates, marriage certificates, property deeds)
2. **Extract Text**: Use OCR to convert document images to text
3. **Train Models**: Fine-tune Spanish RoBERTa models to classify document types
4. **Deploy Models**: Upload trained models to cloud storage (Git LFS) for production use

### Backend Processing
1. **Load Models**: Download trained models from cloud storage or use local models for testing
2. **Receive Documents**: Accept PDF and image uploads via API
3. **Extract Text**: Use OCR to extract text from uploaded documents
4. **Classify Documents**: Use trained models to determine document type
5. **Create Embeddings**: Generate vector embeddings for semantic search
6. **Store in Index**: Save documents and embeddings in searchable index
7. **Provide Search**: Return relevant documents based on user queries

### Frontend Interface
1. **Upload Documents**: Users upload PDFs and images through web interface
2. **Submit Queries**: Users search for documents using natural language
3. **View Results**: Display search results with document metadata and classification
4. **Manage Documents**: Browse and manage uploaded document collection

## 🚀 Model Deployment Strategy

### Production Deployment
- **Cloud Storage**: Trained models are uploaded to cloud storage using Git LFS
- **Model Repository**: Centralized model repository for version control and distribution
- **Backend Integration**: Backend automatically downloads models from cloud storage
- **Version Management**: Easy model updates and rollbacks through Git LFS

### Development/Testing
- **Local Models**: Models saved to predefined local directory for testing
- **Configuration**: Backend config points to local model path for development
- **Quick Iteration**: Fast model testing without cloud deployment overhead

### Model Lifecycle
1. **Train**: Create models in training pipeline
2. **Test**: Validate models locally with test data
3. **Deploy**: Upload to cloud storage (Git LFS)
4. **Integrate**: Backend pulls models from cloud storage
5. **Update**: New model versions automatically available to backend

## 🎯 Key Technologies

- **Document Classification**: Scikit Learn TfidfVectorizer and MultinomialNB
- **OCR Processing**: EasyOCR and Tesseract for text extraction
- **Search Engine**: FAISS vector search with SentenceTransformer embeddings
- **Backend**: FastAPI for API services
- **Frontend**: Next.js for web interface
- **Training**: PyTorch and Transformers for model development
