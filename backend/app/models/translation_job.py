from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base_model import BaseModel


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslationJob(BaseModel):
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # File information
    original_filename: Mapped[str] = mapped_column(String(length=255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Translation details
    source_language: Mapped[str] = mapped_column(String(length=10), nullable=False)
    target_language: Mapped[str] = mapped_column(String(length=10), nullable=False)
    
    # Processing status
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False
    )
    
    # Results
    download_url: Mapped[Optional[str]] = mapped_column(String(length=512), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metrics
    processing_time: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)  # in milliseconds
    
    # Relationships
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="translation_jobs")
    
    glossary_id: Mapped[Optional[int]] = mapped_column(ForeignKey("glossary.id"), nullable=True)
    glossary: Mapped[Optional["Glossary"]] = relationship(back_populates="translation_jobs")
    
    # Additional timestamps
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
