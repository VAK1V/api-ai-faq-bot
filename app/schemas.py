"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class AnalyzeRequest(BaseModel):
    """Request schema for text analysis."""
    text: str = Field(..., min_length=1, max_length=1000, description="Input text for FAQ bot")

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()


class AnalyzeResponse(BaseModel):
    """Response schema for text analysis."""
    result: str = Field(..., description="Generated answer from the model")
    model: str = Field(..., description="Model name used for generation")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class HistoryItem(BaseModel):
    """Schema for a single history record."""
    id: int
    input_text: str
    result_text: str
    model_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    """Response schema for history list."""
    items: list[HistoryItem]
    total: int


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    database: str
    model_loaded: bool
