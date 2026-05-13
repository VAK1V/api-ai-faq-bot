"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
from app.ml_service import get_model_info
from app.schemas import HealthResponse
from app.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Check service health including database and model status."""
    logger.info("Health check requested")

    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    model_info = get_model_info()

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        model_loaded=model_info["loaded"],
    )
