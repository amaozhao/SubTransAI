"""
测试配置文件

提供测试所需的夹具（fixtures）和配置。
"""

import os
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient


# 覆盖数据库配置，使用 SQLite
settings.SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///./test.db"


# 创建测试数据库引擎
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    poolclass=NullPool,
)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# 数据库会话夹具
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# 覆盖应用依赖
app.dependency_overrides[get_db] = override_get_db


# 测试客户端夹具
@pytest.fixture(scope="session")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


# 数据库会话夹具
@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 提供会话
    async with async_session_maker() as session:
        yield session
    
    # 清理表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# 事件循环夹具
@pytest.fixture(scope="session")
def event_loop():
    """创建一个实例事件循环，供所有测试使用"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 测试数据目录夹具
@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    """设置测试所需的目录"""
    # 设置测试数据目录
    test_data_dir = "test_data"
    test_upload_dir = os.path.join(test_data_dir, "uploads")
    test_chunks_dir = os.path.join(test_data_dir, "chunks")
    test_results_dir = os.path.join(test_data_dir, "results")
    
    # 创建目录
    os.makedirs(test_upload_dir, exist_ok=True)
    os.makedirs(test_chunks_dir, exist_ok=True)
    os.makedirs(test_results_dir, exist_ok=True)
    
    # 覆盖配置
    settings.DATA_DIR = test_data_dir
    settings.UPLOAD_DIR = test_upload_dir
    settings.CHUNKS_DIR = test_chunks_dir
    settings.RESULTS_DIR = test_results_dir
    settings.DOWNLOAD_BASE_URL = "http://testserver/api/v1/files"
    
    yield
    
    # 测试结束后不清理目录，以便检查结果
