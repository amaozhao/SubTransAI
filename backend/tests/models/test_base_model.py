"""
基础模型测试

测试基础模型的软删除功能和时间戳字段。
"""

import pytest
from datetime import datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base_model import BaseModel
from app.db.base_class import Base


# 创建一个测试模型
class TestModel(BaseModel, Base):
    __tablename__ = "test_model"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)


@pytest.mark.asyncio
async def test_base_model_timestamps(db: AsyncSession):
    """测试基础模型的时间戳字段"""
    # 创建测试对象
    test_obj = TestModel(name="Test Object")
    
    # 添加到数据库
    db.add(test_obj)
    await db.commit()
    await db.refresh(test_obj)
    
    # 验证时间戳字段
    assert test_obj.created_at is not None
    assert test_obj.updated_at is not None
    assert test_obj.deleted is False
    assert test_obj.deleted_at is None
    
    # 记录创建时间
    created_at = test_obj.created_at
    
    # 更新对象
    test_obj.name = "Updated Test Object"
    await db.commit()
    await db.refresh(test_obj)
    
    # 验证更新时间已更改
    assert test_obj.updated_at > created_at


@pytest.mark.asyncio
async def test_base_model_soft_delete(db: AsyncSession):
    """测试基础模型的软删除功能"""
    # 创建测试对象
    test_obj = TestModel(name="Test Object")
    
    # 添加到数据库
    db.add(test_obj)
    await db.commit()
    await db.refresh(test_obj)
    
    # 记录ID
    obj_id = test_obj.id
    
    # 软删除对象
    test_obj.deleted = True
    test_obj.deleted_at = datetime.utcnow()
    await db.commit()
    
    # 查询对象（包括已删除的）
    result = await db.get(TestModel, obj_id)
    
    # 验证对象仍然存在但已标记为删除
    assert result is not None
    assert result.deleted is True
    assert result.deleted_at is not None
