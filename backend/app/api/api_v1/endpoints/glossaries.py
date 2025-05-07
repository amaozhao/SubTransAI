from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.glossary import Glossary, GlossaryCreate, GlossaryUpdate
from app.services.glossary import glossary_service

router = APIRouter()


@router.get("/", response_model=List[Glossary])
async def read_glossaries(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve glossaries.
    """
    if deps.is_superuser(current_user):
        glossaries = await glossary_service.get_multi(db, skip=skip, limit=limit)
    else:
        glossaries = await glossary_service.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return glossaries


@router.post("/", response_model=Glossary)
async def create_glossary(
    *,
    db: AsyncSession = Depends(get_db),
    glossary_in: GlossaryCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new glossary.
    """
    glossary = await glossary_service.create_with_owner(
        db=db, obj_in=glossary_in, owner_id=current_user.id
    )
    return glossary


@router.get("/{id}", response_model=Glossary)
async def read_glossary(
    *,
    db: AsyncSession = Depends(get_db),
    id: int = Path(..., title="The ID of the glossary to get"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get glossary by ID.
    """
    glossary = await glossary_service.get(db=db, id=id)
    if not glossary:
        raise HTTPException(status_code=404, detail="Glossary not found")
    if not deps.is_superuser(current_user) and (glossary.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return glossary


@router.put("/{id}", response_model=Glossary)
async def update_glossary(
    *,
    db: AsyncSession = Depends(get_db),
    id: int = Path(..., title="The ID of the glossary to update"),
    glossary_in: GlossaryUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a glossary.
    """
    glossary = await glossary_service.get(db=db, id=id)
    if not glossary:
        raise HTTPException(status_code=404, detail="Glossary not found")
    if not deps.is_superuser(current_user) and (glossary.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    glossary = await glossary_service.update(db=db, db_obj=glossary, obj_in=glossary_in)
    return glossary


@router.delete("/{id}", response_model=Glossary)
async def delete_glossary(
    *,
    db: AsyncSession = Depends(get_db),
    id: int = Path(..., title="The ID of the glossary to delete"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a glossary.
    """
    glossary = await glossary_service.get(db=db, id=id)
    if not glossary:
        raise HTTPException(status_code=404, detail="Glossary not found")
    if not deps.is_superuser(current_user) and (glossary.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    glossary = await glossary_service.remove(db=db, id=id)
    return glossary
