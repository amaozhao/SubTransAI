from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.user import auth_backend, get_user_manager


# FastAPI Users
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

get_current_user = fastapi_users.current_user()
get_current_active_user = fastapi_users.current_user(active=True)
get_current_superuser = fastapi_users.current_user(active=True, superuser=True)


def is_superuser(user: User) -> bool:
    """Check if user is superuser."""
    return user.is_superuser


# User dependencies
async def get_user_by_id(
    user_id: int, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get user by ID."""
    from app.services.user import user_service
    
    user = await user_service.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
