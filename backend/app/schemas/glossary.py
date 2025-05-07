from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


# Shared properties
class GlossaryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    terms: Optional[Dict[str, str]] = None


# Properties to receive on glossary creation
class GlossaryCreate(GlossaryBase):
    name: str
    source_language: str
    target_language: str
    terms: Dict[str, str] = Field(default_factory=dict)


# Properties to receive on glossary update
class GlossaryUpdate(GlossaryBase):
    pass


# Properties shared by models stored in DB
class GlossaryInDBBase(GlossaryBase):
    id: int
    name: str
    source_language: str
    target_language: str
    terms: Dict[str, str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Properties to return to client
class Glossary(GlossaryInDBBase):
    pass


# Properties properties stored in DB
class GlossaryInDB(GlossaryInDBBase):
    pass
