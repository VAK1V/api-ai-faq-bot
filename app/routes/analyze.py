"""Analyze endpoint for FAQ bot."""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.models import RequestHistory
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.ml_service import generate_answer
from app.config import get_settings
from app.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()
settings = get_settings()


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Verify API key if configured."""
    if settings.api_key and x_api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt: {x_api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Process text with the FAQ bot model and save to history.

    - **text**: Question or text to analyze (max 500 chars by default)
    """
    logger.info(f"Analyze request received: {request.text[:50]}...")

    # Check max length
    if len(request.text) > settings.max_text_length:
        logger.warning(f"Text too long: {len(request.text)} chars")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text exceeds maximum length of {settings.max_text_length} characters",
        )

    try:
        # Generate answer
        answer, processing_time = generate_answer(request.text)

        # Save to database
        history_record = RequestHistory(
            input_text=request.text,
            result_text=answer,
            model_name=settings.model_file,
        )
        db.add(history_record)
        db.commit()
        db.refresh(history_record)

        logger.info(f"Request saved to history with id={history_record.id}")

        return AnalyzeResponse(
            result=answer,
            model=settings.model_file,
            processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}",
        )
