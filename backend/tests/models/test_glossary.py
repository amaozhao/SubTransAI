"""
术语表模型测试

测试术语表模型的属性和关联。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.glossary import Glossary
from app.models.user import User


@pytest.mark.asyncio
async def test_glossary_create(db: AsyncSession):
    """测试创建术语表"""
    # 创建用户
    user = User(
        email="glossary_test@example.com",
        username="glossaryuser",
        mobile="13800138444",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建术语表
    glossary = Glossary(
        name="测试术语表",
        description="这是一个测试术语表",
        source_language="en",
        target_language="zh",
        terms={"hello": "你好", "world": "世界"},
        user_id=user.id
    )
    
    db.add(glossary)
    await db.commit()
    await db.refresh(glossary)
    
    # 验证术语表属性
    assert glossary.id is not None
    assert glossary.name == "测试术语表"
    assert glossary.description == "这是一个测试术语表"
    assert glossary.source_language == "en"
    assert glossary.target_language == "zh"
    assert glossary.terms == {"hello": "你好", "world": "世界"}
    assert glossary.user_id == user.id
    assert glossary.created_at is not None
    assert glossary.updated_at is not None
    assert glossary.deleted is False
    assert glossary.deleted_at is None


@pytest.mark.asyncio
async def test_glossary_update(db: AsyncSession):
    """测试更新术语表"""
    # 创建用户
    user = User(
        email="update_glossary@example.com",
        username="updateglossary",
        mobile="13800138555",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建术语表
    glossary = Glossary(
        name="初始术语表",
        description="初始描述",
        source_language="en",
        target_language="zh",
        terms={"term1": "术语1"},
        user_id=user.id
    )
    
    db.add(glossary)
    await db.commit()
    await db.refresh(glossary)
    
    # 更新术语表
    glossary.name = "更新后的术语表"
    glossary.description = "更新后的描述"
    glossary.terms = {"term1": "术语1", "term2": "术语2"}
    
    await db.commit()
    await db.refresh(glossary)
    
    # 验证更新后的属性
    assert glossary.name == "更新后的术语表"
    assert glossary.description == "更新后的描述"
    assert glossary.terms == {"term1": "术语1", "term2": "术语2"}
    
    # 查询术语表
    result = await db.execute(
        select(Glossary).where(Glossary.id == glossary.id)
    )
    updated_glossary = result.scalars().first()
    
    # 验证更新已保存到数据库
    assert updated_glossary is not None
    assert updated_glossary.name == "更新后的术语表"
    assert updated_glossary.description == "更新后的描述"
    assert updated_glossary.terms == {"term1": "术语1", "term2": "术语2"}


@pytest.mark.asyncio
async def test_glossary_soft_delete(db: AsyncSession):
    """测试术语表软删除"""
    # 创建用户
    user = User(
        email="delete_glossary@example.com",
        username="deleteglossary",
        mobile="13800138666",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建术语表
    glossary = Glossary(
        name="要删除的术语表",
        description="这个术语表将被删除",
        source_language="en",
        target_language="zh",
        terms={"delete": "删除"},
        user_id=user.id
    )
    
    db.add(glossary)
    await db.commit()
    await db.refresh(glossary)
    
    # 软删除术语表
    glossary.deleted = True
    await db.commit()
    
    # 查询术语表
    result = await db.execute(
        select(Glossary).where(Glossary.id == glossary.id)
    )
    deleted_glossary = result.scalars().first()
    
    # 验证术语表已被标记为删除
    assert deleted_glossary is not None
    assert deleted_glossary.deleted is True
