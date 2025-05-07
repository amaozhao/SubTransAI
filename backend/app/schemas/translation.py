from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.translation_job import JobStatus


# Shared properties
class TranslationJobBase(BaseModel):
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    glossary_id: Optional[int] = None


# Properties to receive on translation job creation
class TranslationJobCreate(TranslationJobBase):
    source_language: str
    target_language: str
    file: bytes = Field(..., description="Base64 encoded SRT file")


# Properties to receive on translation job update
class TranslationJobUpdate(TranslationJobBase):
    status: Optional[JobStatus] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None


# Properties shared by models stored in DB
class TranslationJobInDBBase(TranslationJobBase):
    id: int
    original_filename: str
    file_size: int
    source_language: str
    target_language: str
    status: JobStatus
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[int] = None
    user_id: int
    glossary_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class TranslationJob(TranslationJobInDBBase):
    pass


# Properties properties stored in DB
class TranslationJobInDB(TranslationJobInDBBase):
    pass


# Response for translation API
class TranslationResponse(BaseModel):
    status: int = 200
    download_url: Optional[str] = None
    job_id: int
    message: str = "Translation job created successfully"
