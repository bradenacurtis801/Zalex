# ScriptNinja AI Document Agent
# A self-contained FastAPI application for document ingestion, OCR, indexing, and retrieval.
# To run:
# 1. Make sure you are in the directory '/Users/casamaio/ScanPro'
# 2. Install dependencies: pip install fastapi uvicorn easyocr torch torchvision faiss-cpu sentence-transformers PyMuPDF numpy Pillow python-multipart
# 3. Run the script: uvicorn main:app --reload --host 127.0.0.1 --port 8000
# 4. Open your web browser to http://127.0.0.1:8000

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

import config as config
from app_state import get_app_state
from src.routers import category, feedback, query, upload

# --- Configuration ---
# Set up basic logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

    # Create all required directories
    logger.debug("Creating application directories...")
    config.APP_DIR.mkdir(parents=True, exist_ok=True)
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    config.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug("Application directories created successfully")

    app_state = get_app_state()
    logger.debug("Initializing app state...")

    # Configure model loading (URL download only)
    model_url = config.get_model_url()

    if model_url:
        logger.info(f"Using model URL for download: {model_url}")
        app_state.set_model_url(model_url)
    else:
        # No explicit configuration - will check ML_MODELS_DIR automatically
        logger.info(
            "No model configuration found, will check ML_MODELS_DIR for existing model"
        )
        logger.info(
            "If no model is found, please train one or configure SCANPRO_MODEL_URL"
        )

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
    lifespan=lifespan,
)

# Add CORS middleware for frontend
# Parse CORS origins from environment variable (comma-separated)
cors_origins = [origin.strip() for origin in config.settings.cors_origins.split(",")]

# In development, allow all origins for easier debugging
if config.is_development:
    cors_origins = ["*"]  # Allow all origins in development

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Exception handlers
from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.exceptions import map_to_http_exception


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    http_exc = map_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code, content={"detail": http_exc.detail}
    )


# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(category.router, prefix="/api", tags=["category"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "service": "ScanPro API"}


# Development redirect
@app.get("/")
async def root():
    """Redirect to frontend in development mode."""
    if config.is_development:
        return RedirectResponse(url="/docs")
    else:
        return {"message": "ScanPro API is running"}


if __name__ == "__main__":
    import uvicorn

    host = config.settings.backend_host if config.is_production else "0.0.0.0"

    uvicorn.run(
        "main:app",
        host=host,
        port=config.BACKEND_PORT,
        reload=bool(config.is_development),
    )
