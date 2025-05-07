"""
翻译服务测试

测试翻译服务的各种功能，包括创建翻译作业、更新状态和获取作业。
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.translation import translation_service
from app.schemas.translation import TranslationJobCreate
from app.models.translation_job import JobStatus
from app.models.user import User


@pytest.mark.asyncio
async def test_create_translation_job(db: AsyncSession):
    """测试创建翻译作业"""
    # 创建用户
    user = User(
        email="translation_test@example.com",
        username="translationuser",
        mobile="13900139100",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建翻译作业数据
    job_in = TranslationJobCreate(
        source_language="en",
        target_language="zh",
        glossary_id=None,
        file=b"Test SRT content"
    )
    
    # 创建翻译作业
    job = await translation_service.create_translation_job(
        db=db,
        obj_in=job_in,
        user_id=user.id,
        filename="test.srt"
    )
    
    # 验证作业属性
    assert job.id is not None
    assert job.user_id == user.id
    assert job.original_filename == "test.srt"
    assert job.file_size == len(job_in.file)
    assert job.source_language == "en"
    assert job.target_language == "zh"
    assert job.status == JobStatus.PENDING
    assert job.created_at is not None
    assert job.updated_at is not None
    assert job.deleted is False
    assert job.deleted_at is None


@pytest.mark.asyncio
async def test_get_multi_by_user(db: AsyncSession):
    """测试获取用户的多个翻译作业"""
    # 创建用户
    user = User(
        email="multi_jobs@example.com",
        username="multijobsuser",
        mobile="13900139200",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建多个翻译作业
    for i in range(3):
        job_in = TranslationJobCreate(
            source_language="en",
            target_language="zh",
            glossary_id=None,
            file=b"Test SRT content"
        )
        
        await translation_service.create_translation_job(
            db=db,
            obj_in=job_in,
            user_id=user.id,
            filename=f"test{i}.srt"
        )
    
    # 获取用户的所有作业
    jobs = await translation_service.get_multi_by_user(db, user_id=user.id)
    
    # 验证作业数量
    assert len(jobs) >= 3
    
    # 验证作业属性
    for job in jobs:
        assert job.user_id == user.id
        assert job.status == JobStatus.PENDING


@pytest.mark.asyncio
async def test_update_status(db: AsyncSession):
    """测试更新翻译作业状态"""
    # 创建用户
    user = User(
        email="status_update@example.com",
        username="statusupdateuser",
        mobile="13900139300",
        hashed_password="hashed_password",
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 创建翻译作业
    job_in = TranslationJobCreate(
        source_language="en",
        target_language="zh",
        glossary_id=None,
        file=b"Test SRT content"
    )
    
    job = await translation_service.create_translation_job(
        db=db,
        obj_in=job_in,
        user_id=user.id,
        filename="status_test.srt"
    )
    
    # 更新状态为处理中
    updated_job = await translation_service.update_status(
        db=db,
        job_id=job.id,
        status=JobStatus.PROCESSING
    )
    
    # 验证状态更新
    assert updated_job.id == job.id
    assert updated_job.status == JobStatus.PROCESSING
    
    # 更新状态为已完成
    download_url = "http://example.com/download/456"
    processing_time = 2000  # 毫秒
    
    completed_job = await translation_service.update_status(
        db=db,
        job_id=job.id,
        status=JobStatus.COMPLETED,
        download_url=download_url,
        processing_time=processing_time
    )
    
    # 验证状态更新
    assert completed_job.id == job.id
    assert completed_job.status == JobStatus.COMPLETED
    assert completed_job.download_url == download_url
    assert completed_job.processing_time == processing_time
    assert completed_job.completed_at is not None
    
    # 更新状态为失败
    error_message = "Translation failed: Invalid input"
    
    failed_job = await translation_service.update_status(
        db=db,
        job_id=job.id,
        status=JobStatus.FAILED,
        error_message=error_message
    )
    
    # 验证状态更新
    assert failed_job.id == job.id
    assert failed_job.status == JobStatus.FAILED
    assert failed_job.error_message == error_message
