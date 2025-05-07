"""
翻译作业模型测试

测试翻译作业模型的属性和状态转换。
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.translation_job import TranslationJob, JobStatus
from app.models.user import User


@pytest.mark.asyncio
async def test_translation_job_create(db: AsyncSession):
    """测试创建翻译作业"""
    # 创建用户
    user = User(
        email="job_test@example.com",
        username="jobuser",
        mobile="13800138111",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建翻译作业
    job = TranslationJob(
        user_id=user.id,
        original_filename="test.srt",
        file_size=1024,
        source_language="en",
        target_language="zh",
        status=JobStatus.PENDING
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # 验证作业属性
    assert job.id is not None
    assert job.user_id == user.id
    assert job.original_filename == "test.srt"
    assert job.file_size == 1024
    assert job.source_language == "en"
    assert job.target_language == "zh"
    assert job.status == JobStatus.PENDING
    assert job.created_at is not None
    assert job.updated_at is not None
    assert job.deleted is False
    assert job.deleted_at is None
    assert job.completed_at is None
    assert job.download_url is None
    assert job.error_message is None


@pytest.mark.asyncio
async def test_translation_job_status_transitions(db: AsyncSession):
    """测试翻译作业状态转换"""
    # 创建用户
    user = User(
        email="status_test@example.com",
        username="statususer",
        mobile="13800138222",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建翻译作业
    job = TranslationJob(
        user_id=user.id,
        original_filename="status_test.srt",
        file_size=2048,
        source_language="en",
        target_language="zh",
        status=JobStatus.PENDING
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # 更新状态为处理中
    job.status = JobStatus.PROCESSING
    await db.commit()
    await db.refresh(job)
    
    assert job.status == JobStatus.PROCESSING
    
    # 更新状态为已完成
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.utcnow()
    job.download_url = "http://example.com/download/123"
    job.processing_time = 1500  # 毫秒
    await db.commit()
    await db.refresh(job)
    
    assert job.status == JobStatus.COMPLETED
    assert job.completed_at is not None
    assert job.download_url == "http://example.com/download/123"
    assert job.processing_time == 1500
    
    # 查询作业
    result = await db.execute(
        select(TranslationJob).where(TranslationJob.id == job.id)
    )
    updated_job = result.scalars().first()
    
    # 验证状态已更新
    assert updated_job is not None
    assert updated_job.status == JobStatus.COMPLETED


@pytest.mark.asyncio
async def test_translation_job_failure(db: AsyncSession):
    """测试翻译作业失败状态"""
    # 创建用户
    user = User(
        email="failure_test@example.com",
        username="failureuser",
        mobile="13800138333",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建翻译作业
    job = TranslationJob(
        user_id=user.id,
        original_filename="failure_test.srt",
        file_size=3072,
        source_language="en",
        target_language="zh",
        status=JobStatus.PENDING
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # 更新状态为失败
    job.status = JobStatus.FAILED
    job.completed_at = datetime.utcnow()
    job.error_message = "Translation failed: Invalid SRT format"
    await db.commit()
    await db.refresh(job)
    
    assert job.status == JobStatus.FAILED
    assert job.completed_at is not None
    assert job.error_message == "Translation failed: Invalid SRT format"
