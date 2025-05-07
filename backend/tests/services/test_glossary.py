"""
术语表服务测试

测试术语表服务的各种功能，包括创建、更新和获取术语表。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.glossary import glossary_service
from app.schemas.glossary import GlossaryCreate, GlossaryUpdate
from app.models.user import User


@pytest.mark.asyncio
async def test_create_glossary(db: AsyncSession):
    """测试创建术语表"""
    # 创建用户
    user = User(
        email="glossary_service@example.com",
        username="glossaryserviceuser",
        mobile="13900139400",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建术语表数据
    glossary_in = GlossaryCreate(
        name="测试术语表",
        description="这是一个测试术语表",
        source_language="en",
        target_language="zh",
        terms={"hello": "你好", "world": "世界"}
    )
    
    # 创建术语表
    glossary = await glossary_service.create_with_owner(
        db=db,
        obj_in=glossary_in,
        owner_id=user.id
    )
    
    # 验证术语表属性
    assert glossary.id is not None
    assert glossary.name == glossary_in.name
    assert glossary.description == glossary_in.description
    assert glossary.source_language == glossary_in.source_language
    assert glossary.target_language == glossary_in.target_language
    assert glossary.terms == glossary_in.terms
    assert glossary.user_id == user.id


@pytest.mark.asyncio
async def test_get_glossary(db: AsyncSession):
    """测试获取术语表"""
    # 创建用户
    user = User(
        email="get_glossary@example.com",
        username="getglossaryuser",
        mobile="13900139500",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建术语表数据
    glossary_in = GlossaryCreate(
        name="获取测试术语表",
        description="用于测试获取功能的术语表",
        source_language="en",
        target_language="zh",
        terms={"test": "测试", "get": "获取"}
    )
    
    # 创建术语表
    created_glossary = await glossary_service.create_with_owner(
        db=db,
        obj_in=glossary_in,
        owner_id=user.id
    )
    
    # 获取术语表
    glossary = await glossary_service.get(db, id=created_glossary.id)
    
    # 验证术语表
    assert glossary is not None
    assert glossary.id == created_glossary.id
    assert glossary.name == glossary_in.name
    assert glossary.terms == glossary_in.terms


@pytest.mark.asyncio
async def test_get_multi_by_owner(db: AsyncSession):
    """测试获取用户的多个术语表"""
    # 创建用户
    user = User(
        email="multi_glossaries@example.com",
        username="multiglossariesuser",
        mobile="13900139600",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建多个术语表
    for i in range(3):
        glossary_in = GlossaryCreate(
            name=f"术语表 {i}",
            description=f"这是术语表 {i}",
            source_language="en",
            target_language="zh",
            terms={"term": f"术语 {i}"}
        )
        
        await glossary_service.create_with_owner(
            db=db,
            obj_in=glossary_in,
            owner_id=user.id
        )
    
    # 获取用户的所有术语表
    glossaries = await glossary_service.get_multi_by_owner(
        db=db,
        owner_id=user.id
    )
    
    # 验证术语表数量
    assert len(glossaries) >= 3
    
    # 验证术语表属性
    for glossary in glossaries:
        assert glossary.user_id == user.id


@pytest.mark.asyncio
async def test_update_glossary(db: AsyncSession):
    """测试更新术语表"""
    # 创建用户
    user = User(
        email="update_glossary@example.com",
        username="updateglossaryuser",
        mobile="13900139700",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建术语表数据
    glossary_in = GlossaryCreate(
        name="更新前术语表",
        description="更新前的描述",
        source_language="en",
        target_language="zh",
        terms={"before": "之前"}
    )
    
    # 创建术语表
    glossary = await glossary_service.create_with_owner(
        db=db,
        obj_in=glossary_in,
        owner_id=user.id
    )
    
    # 更新术语表数据
    glossary_update = GlossaryUpdate(
        name="更新后术语表",
        description="更新后的描述",
        terms={"before": "之前", "after": "之后"}
    )
    
    # 更新术语表
    updated_glossary = await glossary_service.update(
        db=db,
        db_obj=glossary,
        obj_in=glossary_update
    )
    
    # 验证更新
    assert updated_glossary.id == glossary.id
    assert updated_glossary.name == "更新后术语表"
    assert updated_glossary.description == "更新后的描述"
    assert updated_glossary.terms == {"before": "之前", "after": "之后"}
    assert updated_glossary.source_language == glossary.source_language  # 未更改
    assert updated_glossary.target_language == glossary.target_language  # 未更改


@pytest.mark.asyncio
async def test_delete_glossary(db: AsyncSession):
    """测试删除术语表"""
    # 创建用户
    user = User(
        email="delete_glossary_service@example.com",
        username="deleteglossaryserviceuser",
        mobile="13900139800",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建术语表数据
    glossary_in = GlossaryCreate(
        name="要删除的术语表",
        description="这个术语表将被删除",
        source_language="en",
        target_language="zh",
        terms={"delete": "删除"}
    )
    
    # 创建术语表
    glossary = await glossary_service.create_with_owner(
        db=db,
        obj_in=glossary_in,
        owner_id=user.id
    )
    
    # 删除术语表
    deleted_glossary = await glossary_service.remove(db=db, id=glossary.id)
    
    # 验证删除
    assert deleted_glossary.id == glossary.id
    assert deleted_glossary.deleted is True
    assert deleted_glossary.deleted_at is not None
    
    # 尝试获取已删除的术语表
    glossary_after_delete = await glossary_service.get(db=db, id=glossary.id)
    
    # 验证无法获取已删除的术语表
    assert glossary_after_delete is None
