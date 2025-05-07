from typing import Optional, Union, Dict, Any, List

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def create_with_password(
        self, db: AsyncSession, *, obj_in: UserCreate
    ) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=obj_in.password,  # This will be hashed by FastAPIUsers
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_users(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()


user_service = UserService(User)


# FastAPI Users setup
class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY
    
    # 支持email/username/mobile三种登录方式
    async def authenticate(self, credentials) -> Optional[User]:
        try:
            # 获取凭证
            identifier = credentials.get("username")
            password = credentials.get("password")
            
            if not identifier or not password:
                return None
                
            # 尝试通过email、username或mobile查找用户
            user = None
            user_db = self.user_db
            
            # 检查是否是邮箱格式
            if "@" in identifier:
                user = await user_db.get_by_email(identifier)
            else:
                # 尝试通过username查找
                query = select(User).where(User.username == identifier)
                result = await user_db.session.execute(query)
                user = result.scalars().first()
                
                # 如果未找到，尝试通过mobile查找
                if user is None:
                    query = select(User).where(User.mobile == identifier)
                    result = await user_db.session.execute(query)
                    user = result.scalars().first()
            
            if user is None:
                return None
                
            # 验证密码
            verified, updated_password_hash = self.password_helper.verify_and_update(
                password, user.hashed_password
            )
            if not verified:
                return None
                
            # 如果密码哈希需要更新
            if updated_password_hash is not None:
                await self._update_password(user, updated_password_hash)
                
            return user
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger = get_logger("app.services.user")
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger = get_logger("app.services.user")
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger = get_logger("app.services.user")
        logger.info(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


# Authentication
bearer_transport = BearerTransport(tokenUrl=f"{settings.API_V1_STR}/users/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


# Create a single auth backend instance to be used throughout the application
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Create a user_manager function that returns a UserManager instance
# This is needed for compatibility with existing code
async def get_user_manager_instance(user_db):
    return UserManager(user_db)
