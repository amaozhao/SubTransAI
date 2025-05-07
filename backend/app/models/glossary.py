from typing import List, Optional

from sqlalchemy import String, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Glossary(BaseModel):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(length=100), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Store glossary terms as JSON: {"term": "translation"}
    terms: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    source_language: Mapped[str] = mapped_column(String(length=10), nullable=False)
    target_language: Mapped[str] = mapped_column(String(length=10), nullable=False)
    
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    owner: Mapped["User"] = relationship(back_populates="glossaries")
    
    # Relationships
    translation_jobs: Mapped[List["TranslationJob"]] = relationship(back_populates="glossary")
