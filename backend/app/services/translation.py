from typing import List, Optional, Dict, Any, Union
import time
import base64
import os
from app.core.logging import get_logger
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import translation_workflow
from app.core.config import settings

from app.models.translation_job import TranslationJob, JobStatus
from app.schemas.translation import TranslationJobCreate, TranslationJobUpdate
from app.services.base import BaseService


logger = get_logger("app.services.translation")


class TranslationService(BaseService[TranslationJob, TranslationJobCreate, TranslationJobUpdate]):
    async def create_translation_job(
        self, db: AsyncSession, *, obj_in: TranslationJobCreate, user_id: int, filename: str
    ) -> TranslationJob:
        """Create a new translation job."""
        # Create job record
        db_obj = TranslationJob(
            original_filename=filename,
            file_size=len(obj_in.file),
            source_language=obj_in.source_language,
            target_language=obj_in.target_language,
            glossary_id=obj_in.glossary_id,
            user_id=user_id,
            status=JobStatus.PENDING
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Store file content in a temporary location or object storage
        # For simplicity, we're not implementing actual file storage here
        
        return db_obj
    
    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[TranslationJob]:
        """Get multiple translation jobs by user ID."""
        result = await db.execute(
            select(TranslationJob)
            .filter(TranslationJob.user_id == user_id)
            .order_by(TranslationJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_status(
        self, db: AsyncSession, *, job_id: int, status: JobStatus, 
        download_url: Optional[str] = None, error_message: Optional[str] = None,
        processing_time: Optional[int] = None
    ) -> TranslationJob:
        """Update the status of a translation job."""
        job = await self.get(db=db, id=job_id)
        if not job:
            return None
        
        job.status = status
        
        if download_url:
            job.download_url = download_url
        
        if error_message:
            job.error_message = error_message
        
        if processing_time:
            job.processing_time = processing_time
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job
    
    async def process_translation_job(self, db: AsyncSession, job_id: int) -> None:
        """Process a translation job using Agno framework."""
        # Get the job
        job = await self.get(db=db, id=job_id)
        if not job:
            logger.error("Translation job not found", job_id=job_id)
            return
        
        # Update job status to processing
        await self.update_status(db=db, job_id=job_id, status=JobStatus.PROCESSING)
        
        # Start processing
        start_time = time.time()
        
        try:
            # 确保目录存在
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            os.makedirs(settings.CHUNKS_DIR, exist_ok=True)
            os.makedirs(settings.RESULTS_DIR, exist_ok=True)
            
            # 获取文件内容（从数据库或文件系统）
            # 在实际实现中，这里应该从存储中检索文件内容
            # 这里我们假设文件内容已经存储在数据库中或可以从其他地方获取
            file_content = "Example SRT content"  # 实际应用中需要替换为真实内容
            
            # 获取术语表（如果有）
            glossary = None
            if job.glossary_id:
                # 在实际实现中，这里应该从数据库中获取术语表
                # 为了示例，我们使用一个空字典
                glossary = {}
            
            # 运行翻译工作流
            result = await translation_workflow.process(
                content=file_content,
                source_lang=job.source_language,
                target_lang=job.target_language,
                task_id=str(job_id),
                glossary=glossary,
                engine=settings.AGNO_DEFAULT_ENGINE,
                chunk_size=settings.AGNO_CHUNK_SIZE
            )
            
            # Process completed successfully
            processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            # Update job with results
            await self.update_status(
                db=db,
                job_id=job_id,
                status=JobStatus.COMPLETED,
                download_url=result.get("download_url"),
                processing_time=processing_time
            )
            
            logger.info(
                "Translation job completed",
                job_id=job_id,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            # Process failed
            processing_time = int((time.time() - start_time) * 1000)
            
            # Update job with error
            await self.update_status(
                db=db,
                job_id=job_id,
                status=JobStatus.FAILED,
                error_message=str(e),
                processing_time=processing_time
            )
            
            logger.error(
                "Translation job failed",
                job_id=job_id,
                error=str(e),
                processing_time_ms=processing_time
            )


translation_service = TranslationService(TranslationJob)
