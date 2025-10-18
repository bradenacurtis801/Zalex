# ScriptNinja AI Document Agent
# A self-contained FastAPI application for document ingestion, OCR, indexing, and retrieval.
# To run:
# 1. Make sure you are in the directory '/Users/casamaio/ScanPro'
# 2. Install dependencies: pip install fastapi uvicorn easyocr torch torchvision faiss-cpu sentence-transformers PyMuPDF numpy Pillow python-multipart
# 3. Run the script: uvicorn main:app --reload --host 127.0.0.1 --port 8000
# 4. Open your web browser to http://127.0.0.1:8000

import logging
import logging.config
import os
from contextlib import asynccontextmanager

import config as config
from src.db.connection import create_db_and_tables, get_session
from app_state import get_app_state
from src.models.database import User, UserRole
from src.services.auth_service import AuthService
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from src.routers import auth, category, feedback, query, upload
from src.websocket_manager import get_connection_manager
import json
import asyncio


# Create all application directories
config.setup_app_dirs()

# --- Configuration ---
# Set up basic logging
logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)



# Get the singleton connection manager
manager = get_connection_manager()


def create_default_admin_user():
    """Create a default admin user if no users exist in the database."""
    try:
        with next(get_session()) as db:
            # Check if any users exist
            from sqlmodel import select
            existing_users = db.exec(select(User)).first()
            if existing_users:
                logger.info("Users already exist, skipping default admin creation")
                return
            
            # Create default admin user directly in database
            from src.services.auth_service import pwd_context
            
            # Hash password using the same context as AuthService
            hashed_password = pwd_context.hash("admin123")
            
            # Create admin user directly
            admin_user = User(
                username="admin",
                email="admin@scanpro.local",
                full_name="Administrator",
                password_hash=hashed_password,
                user_role=UserRole.ADMIN,
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            logger.info(f"\033[92m✅ Created default admin user: {admin_user.username}\033[0m")
            logger.info("\033[93m🔑 Default credentials: admin / admin123\033[0m")
            logger.info("\033[96m🚀 ScanPro is ready! Visit http://localhost:3000 to get started\033[0m")
            
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")
        # Don't fail startup if user creation fails


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    logger.info("\033[96m🚀 Starting up application...\033[0m")
    logger.debug(f"Working directory: {os.getcwd()}")
    logger.debug(f"App directory: {config.APP_DIR}")

    create_db_and_tables()

    app_state = get_app_state()
    logger.debug("Initializing app state...")

    # Model loading - will check ML_MODELS_DIR for existing model
    logger.info("Checking ML_MODELS_DIR for existing model")
    logger.info(
        "If no model is found, please train one using: python train/train_similarity_classifier.py"
    )

    app_state.initialize()
    logger.debug("App state initialization complete")
    
    # Create default admin user if no users exist (at the very end)
    create_default_admin_user()
    
    logger.info("\033[92m🎉 Application startup complete!\033[0m")

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
cors_origins = config.settings.cors_origins

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
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(category.router, prefix="/api", tags=["category"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])


# WebSocket endpoint for progress updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates with authentication handshake."""
    await manager.handle_websocket_connection(websocket)


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
