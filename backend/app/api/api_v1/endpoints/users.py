from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.services.user import auth_backend

router = APIRouter()

# Use FastAPIUsers instance from deps.py
fastapi_users = deps.fastapi_users

# Use the current user dependencies from deps.py
current_active_user = deps.get_current_active_user
current_superuser = deps.get_current_superuser

# Include FastAPI Users routers
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_register_router(UserSchema, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserSchema),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserSchema, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/", response_model=List[UserSchema])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_superuser),
) -> Any:
    """
    Retrieve users.
    """
    from app.services.user import user_service
    users = await user_service.get_users(db, skip=skip, limit=limit)
    return users
