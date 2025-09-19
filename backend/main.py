# ScriptNinja AI Document Agent
# A self-contained FastAPI application for document ingestion, OCR, indexing, and retrieval.
# To run:
# 1. Make sure you are in the directory '/Users/casamaio/ScanPro'
# 2. Install dependencies: pip install fastapi uvicorn easyocr torch torchvision faiss-cpu sentence-transformers PyMuPDF numpy Pillow python-multipart
# 3. Run the script: uvicorn main:app --reload --host 127.0.0.1 --port 5000
# 4. Open your web browser to http://127.0.0.1:5000

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

import config as config
from src.routers import upload, query
from app_state import get_app_state

# --- Configuration ---
# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the base directory where the script is expected to run
os.chdir(config.APP_DIR)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    logger.info("Starting up application...")
    logger.debug(f"Working directory: {os.getcwd()}")
    logger.debug(f"App directory: {config.APP_DIR}")
    logger.debug(f"Upload directory: {config.UPLOAD_DIR}")
    logger.debug(f"Index file: {config.INDEX_FILE}")
    logger.debug(f"Metadata file: {config.METADATA_FILE}")
    
    app_state = get_app_state()
    logger.debug("Initializing app state...")
    app_state.initialize()
    logger.debug("App state initialization complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    logger.debug("Application shutdown complete")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="ScriptNinja AI Document Agent",
    description="A self-contained FastAPI application for document ingestion, OCR, indexing, and retrieval.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(query.router, prefix="/api", tags=["query"])

# Development redirect
@app.get("/")
async def root():
    """Redirect to frontend in development mode."""
    if config.is_development:
        return RedirectResponse(url="/docs")
    else:
        return {"message": "ScanPro API is running"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)