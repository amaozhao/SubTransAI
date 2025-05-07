from typing import Optional, List

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from fastapi_users.db import SQLAlchemyBaseUserTable

from app.models.base_model import BaseModel


class User(SQLAlchemyBaseUserTable[int], BaseModel):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=320), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(length=150), unique=True, index=True, nullable=True)
    mobile: Mapped[str] = mapped_column(String(length=20), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Additional fields
    full_name: Mapped[str] = mapped_column(String(length=100), nullable=True)
    
    # Relationships
    glossaries: Mapped[List["Glossary"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    translation_jobs: Mapped[List["TranslationJob"]] = relationship(back_populates="user", cascade="all, delete-orphan")
