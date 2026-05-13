"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db import Base


class RequestHistory(Base):
    """Table for storing request history."""
    __tablename__ = "requests_history"

    id = Column(Integer, primary_key=True, index=True)
    input_text = Column(Text, nullable=False)
    result_text = Column(Text, nullable=False)
    model_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<RequestHistory(id={self.id}, model={self.model_name})>"
