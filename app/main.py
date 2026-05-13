"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db import init_db
from app.routes import health, analyze, history
from app.ml_service import load_model
from app.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("=" * 50)
    logger.info("AI FAQ Bot starting up...")
    logger.info("=" * 50)

    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Load model
    try:
        load_model()
    except Exception as e:
        logger.error(f"Model pre-loading failed (will retry on first request): {e}")

    yield

    logger.info("AI FAQ Bot shutting down...")


app = FastAPI(
    title="AI FAQ Bot API",
    description="FAQ Bot powered by T-lite-it-2.1-GGUF model via Hugging Face",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions globally."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AI FAQ Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
