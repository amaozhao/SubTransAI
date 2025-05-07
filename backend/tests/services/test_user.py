"""
用户服务测试

测试用户服务的各种功能，包括创建、认证和更新用户。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import user_service
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import verify_password


@pytest.mark.asyncio
async def test_create_user(db: AsyncSession):
    """测试创建用户"""
    # 创建用户数据
    user_in = UserCreate(
        email="create_test@example.com",
        username="createuser",
        mobile="13800138777",
        password="testpassword"
    )
    
    # 创建用户
    user = await user_service.create(db, obj_in=user_in)
    
    # 验证用户属性
    assert user.email == user_in.email
    assert user.username == user_in.username
    assert user.mobile == user_in.mobile
    assert user.hashed_password != user_in.password  # 密码应该已被哈希
    assert verify_password(user_in.password, user.hashed_password)  # 验证密码哈希
    assert user.is_active is True
    assert user.is_superuser is False


@pytest.mark.asyncio
async def test_authenticate_user(db: AsyncSession):
    """测试用户认证"""
    # 创建用户数据
    email = "auth_test@example.com"
    username = "authuser"
    mobile = "13800138888"
    password = "authpassword"
    
    user_in = UserCreate(
        email=email,
        username=username,
        mobile=mobile,
        password=password
    )
    
    # 创建用户
    await user_service.create(db, obj_in=user_in)
    
    # 测试邮箱认证
    authenticated_user = await user_service.authenticate(db, email=email, password=password)
    assert authenticated_user is not None
    assert authenticated_user.email == email
    
    # 测试用户名认证
    authenticated_user = await user_service.authenticate(db, username=username, password=password)
    assert authenticated_user is not None
    assert authenticated_user.username == username
    
    # 测试手机号认证
    authenticated_user = await user_service.authenticate(db, mobile=mobile, password=password)
    assert authenticated_user is not None
    assert authenticated_user.mobile == mobile
    
    # 测试错误密码
    authenticated_user = await user_service.authenticate(db, email=email, password="wrongpassword")
    assert authenticated_user is None


@pytest.mark.asyncio
async def test_get_user_by_email(db: AsyncSession):
    """测试通过邮箱获取用户"""
    # 创建用户数据
    email = "get_email@example.com"
    user_in = UserCreate(
        email=email,
        username="getemailuser",
        mobile="13800138999",
        password="getpassword"
    )
    
    # 创建用户
    created_user = await user_service.create(db, obj_in=user_in)
    
    # 通过邮箱获取用户
    user = await user_service.get_by_email(db, email=email)
    
    # 验证用户
    assert user is not None
    assert user.id == created_user.id
    assert user.email == email


@pytest.mark.asyncio
async def test_get_user_by_username(db: AsyncSession):
    """测试通过用户名获取用户"""
    # 创建用户数据
    username = "getusernameuser"
    user_in = UserCreate(
        email="get_username@example.com",
        username=username,
        mobile="13900139000",
        password="getpassword"
    )
    
    # 创建用户
    created_user = await user_service.create(db, obj_in=user_in)
    
    # 通过用户名获取用户
    user = await user_service.get_by_username(db, username=username)
    
    # 验证用户
    assert user is not None
    assert user.id == created_user.id
    assert user.username == username


@pytest.mark.asyncio
async def test_get_user_by_mobile(db: AsyncSession):
    """测试通过手机号获取用户"""
    # 创建用户数据
    mobile = "13900139001"
    user_in = UserCreate(
        email="get_mobile@example.com",
        username="getmobileuser",
        mobile=mobile,
        password="getpassword"
    )
    
    # 创建用户
    created_user = await user_service.create(db, obj_in=user_in)
    
    # 通过手机号获取用户
    user = await user_service.get_by_mobile(db, mobile=mobile)
    
    # 验证用户
    assert user is not None
    assert user.id == created_user.id
    assert user.mobile == mobile


@pytest.mark.asyncio
async def test_update_user(db: AsyncSession):
    """测试更新用户"""
    # 创建用户数据
    user_in = UserCreate(
        email="update_test@example.com",
        username="updatetestuser",
        mobile="13900139002",
        password="updatepassword"
    )
    
    # 创建用户
    user = await user_service.create(db, obj_in=user_in)
    
    # 更新用户数据
    user_update = UserUpdate(
        email="updated@example.com",
        username="updateduser",
        mobile="13900139003",
        password="newpassword"
    )
    
    # 更新用户
    updated_user = await user_service.update(db, db_obj=user, obj_in=user_update)
    
    # 验证更新
    assert updated_user.id == user.id
    assert updated_user.email == "updated@example.com"
    assert updated_user.username == "updateduser"
    assert updated_user.mobile == "13900139003"
    assert verify_password("newpassword", updated_user.hashed_password)  # 验证新密码
