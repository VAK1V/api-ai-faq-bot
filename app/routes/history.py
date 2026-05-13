"""History endpoints for request records."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app.db import get_db
from app.models import RequestHistory
from app.schemas import HistoryItem, HistoryListResponse
from app.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/history", response_model=HistoryListResponse)
async def get_history(
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
):
    """Get paginated history of requests.

    - **limit**: Records per page (default 20, max 100)
    - **offset**: Records to skip (for pagination)
    """
    logger.info(f"History request: limit={limit}, offset={offset}")

    try:
        total = db.query(RequestHistory).count()
        records = (
            db.query(RequestHistory)
            .order_by(desc(RequestHistory.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return HistoryListResponse(
            items=[HistoryItem.model_validate(r) for r in records],
            total=total,
        )

    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history",
        )


@router.get("/history/{record_id}", response_model=HistoryItem)
async def get_history_by_id(
    record_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific history record by ID.

    - **record_id**: ID of the history record
    """
    logger.info(f"History detail request for id={record_id}")

    try:
        record = db.query(RequestHistory).filter(RequestHistory.id == record_id).first()

        if not record:
            logger.warning(f"History record not found: id={record_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"History record with id={record_id} not found",
            )

        return HistoryItem.model_validate(record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch history record {record_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history record",
        )
