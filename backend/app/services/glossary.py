from typing import List, Optional, Dict, Any, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.glossary import Glossary
from app.schemas.glossary import GlossaryCreate, GlossaryUpdate
from app.services.base import BaseService


class GlossaryService(BaseService[Glossary, GlossaryCreate, GlossaryUpdate]):
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: GlossaryCreate, owner_id: int
    ) -> Glossary:
        obj_in_data = obj_in.model_dump()
        db_obj = Glossary(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_owner(
        self, db: AsyncSession, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Glossary]:
        result = await db.execute(
            select(Glossary)
            .filter(Glossary.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_language_pair(
        self, db: AsyncSession, *, owner_id: int, source_language: str, target_language: str
    ) -> List[Glossary]:
        result = await db.execute(
            select(Glossary)
            .filter(
                Glossary.owner_id == owner_id,
                Glossary.source_language == source_language,
                Glossary.target_language == target_language
            )
        )
        return result.scalars().all()
    
    async def add_terms(
        self, db: AsyncSession, *, glossary_id: int, terms: Dict[str, str]
    ) -> Glossary:
        glossary = await self.get(db=db, id=glossary_id)
        if not glossary:
            return None
        
        # Merge new terms with existing ones
        glossary.terms.update(terms)
        
        db.add(glossary)
        await db.commit()
        await db.refresh(glossary)
        return glossary
    
    async def remove_terms(
        self, db: AsyncSession, *, glossary_id: int, term_keys: List[str]
    ) -> Glossary:
        glossary = await self.get(db=db, id=glossary_id)
        if not glossary:
            return None
        
        # Remove specified terms
        for key in term_keys:
            if key in glossary.terms:
                del glossary.terms[key]
        
        db.add(glossary)
        await db.commit()
        await db.refresh(glossary)
        return glossary


glossary_service = GlossaryService(Glossary)
