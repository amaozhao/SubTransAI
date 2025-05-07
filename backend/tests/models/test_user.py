"""
用户模型测试

测试用户模型的属性和方法。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
async def test_user_create(db: AsyncSession):
    """测试创建用户"""
    # 创建用户
    user = User(
        email="test@example.com",
        username="testuser",
        mobile="13800138000",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False
    )
    
    # 添加到数据库
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 验证用户属性
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.mobile == "13800138000"
    assert user.hashed_password == "hashed_password"
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.deleted is False
    assert user.deleted_at is None


@pytest.mark.asyncio
async def test_user_unique_constraints(db: AsyncSession):
    """测试用户唯一约束"""
    # 创建第一个用户
    user1 = User(
        email="test1@example.com",
        username="testuser1",
        mobile="13800138001",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user1)
    await db.commit()
    
    # 创建具有相同邮箱的第二个用户
    user2 = User(
        email="test1@example.com",  # 相同的邮箱
        username="testuser2",
        mobile="13800138002",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user2)
    
    # 应该引发完整性错误
    with pytest.raises(Exception):
        await db.commit()
    
    # 回滚事务
    await db.rollback()
    
    # 创建具有相同用户名的第三个用户
    user3 = User(
        email="test3@example.com",
        username="testuser1",  # 相同的用户名
        mobile="13800138003",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user3)
    
    # 应该引发完整性错误
    with pytest.raises(Exception):
        await db.commit()
    
    # 回滚事务
    await db.rollback()
    
    # 创建具有相同手机号的第四个用户
    user4 = User(
        email="test4@example.com",
        username="testuser4",
        mobile="13800138001",  # 相同的手机号
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user4)
    
    # 应该引发完整性错误
    with pytest.raises(Exception):
        await db.commit()


@pytest.mark.asyncio
async def test_user_soft_delete(db: AsyncSession):
    """测试用户软删除"""
    # 创建用户
    user = User(
        email="delete@example.com",
        username="deleteuser",
        mobile="13800138099",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 软删除用户
    user.deleted = True
    await db.commit()
    
    # 查询用户
    result = await db.execute(
        select(User).where(User.email == "delete@example.com")
    )
    deleted_user = result.scalars().first()
    
    # 验证用户已被标记为删除
    assert deleted_user is not None
    assert deleted_user.deleted is True
