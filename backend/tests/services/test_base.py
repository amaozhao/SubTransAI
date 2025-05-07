"""
基础服务测试

测试基础服务类的 CRUD 操作和软删除功能。
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, select

from app.models.base_model import BaseModel
from app.db.base_class import Base
from app.services.base import BaseService


# 创建一个测试模型
class TestModel(BaseModel, Base):
    __tablename__ = "test_service_model"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)


# 创建模型对应的 Schema
class TestModelCreate:
    def __init__(self, name: str):
        self.name = name


class TestModelUpdate:
    def __init__(self, name: str = None):
        self.name = name


# 创建一个测试服务
class TestService(BaseService[TestModel, TestModelCreate, TestModelUpdate]):
    pass


# 实例化测试服务
test_service = TestService(TestModel)


@pytest.mark.asyncio
async def test_create(db: AsyncSession):
    """测试创建操作"""
    # 创建对象
    obj_in = TestModelCreate(name="Test Object")
    obj = await test_service.create(db, obj_in=obj_in)
    
    # 验证对象属性
    assert obj.id is not None
    assert obj.name == "Test Object"
    assert obj.created_at is not None
    assert obj.updated_at is not None
    assert obj.deleted is False
    assert obj.deleted_at is None


@pytest.mark.asyncio
async def test_get(db: AsyncSession):
    """测试获取操作"""
    # 创建对象
    obj_in = TestModelCreate(name="Get Test")
    created_obj = await test_service.create(db, obj_in=obj_in)
    
    # 获取对象
    obj = await test_service.get(db, id=created_obj.id)
    
    # 验证对象
    assert obj is not None
    assert obj.id == created_obj.id
    assert obj.name == "Get Test"


@pytest.mark.asyncio
async def test_get_multi(db: AsyncSession):
    """测试获取多个对象"""
    # 创建多个对象
    for i in range(5):
        obj_in = TestModelCreate(name=f"Multi Test {i}")
        await test_service.create(db, obj_in=obj_in)
    
    # 获取所有对象
    objs = await test_service.get_multi(db)
    
    # 验证对象数量
    assert len(objs) >= 5


@pytest.mark.asyncio
async def test_update(db: AsyncSession):
    """测试更新操作"""
    # 创建对象
    obj_in = TestModelCreate(name="Update Test")
    obj = await test_service.create(db, obj_in=obj_in)
    
    # 更新对象
    obj_update = TestModelUpdate(name="Updated Test")
    updated_obj = await test_service.update(db, db_obj=obj, obj_in=obj_update)
    
    # 验证更新
    assert updated_obj.id == obj.id
    assert updated_obj.name == "Updated Test"
    assert updated_obj.updated_at > obj.created_at


@pytest.mark.asyncio
async def test_delete(db: AsyncSession):
    """测试软删除操作"""
    # 创建对象
    obj_in = TestModelCreate(name="Delete Test")
    obj = await test_service.create(db, obj_in=obj_in)
    
    # 软删除对象
    deleted_obj = await test_service.remove(db, id=obj.id)
    
    # 验证软删除
    assert deleted_obj.id == obj.id
    assert deleted_obj.deleted is True
    assert deleted_obj.deleted_at is not None
    
    # 尝试获取已删除的对象
    result = await db.execute(
        select(TestModel).where(TestModel.id == obj.id)
    )
    db_obj = result.scalars().first()
    
    # 验证对象仍然存在但已标记为删除
    assert db_obj is not None
    assert db_obj.deleted is True


@pytest.mark.asyncio
async def test_hard_delete(db: AsyncSession):
    """测试硬删除操作"""
    # 创建对象
    obj_in = TestModelCreate(name="Hard Delete Test")
    obj = await test_service.create(db, obj_in=obj_in)
    
    # 硬删除对象
    await test_service.hard_remove(db, id=obj.id)
    
    # 尝试获取已删除的对象
    result = await db.execute(
        select(TestModel).where(TestModel.id == obj.id)
    )
    db_obj = result.scalars().first()
    
    # 验证对象已被完全删除
    assert db_obj is None
