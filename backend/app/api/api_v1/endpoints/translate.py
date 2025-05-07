"""
翻译 API 端点

提供 SRT 文件翻译功能，集成智能体工作流。
"""

import base64
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.api import deps
from app.agents import translation_workflow
from app.services.translation import translation_service
from app.models.translation_job import JobStatus

router = APIRouter()
logger = get_logger("app.api.translate")


@router.post("/file")
async def translate_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
    glossary_id: Optional[int] = Form(None),
    engine: Optional[str] = Form(None),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    翻译 SRT 文件
    
    - **file**: SRT 文件
    - **source_lang**: 源语言代码
    - **target_lang**: 目标语言代码
    - **glossary_id**: 术语表 ID（可选）
    - **engine**: 翻译引擎（可选，默认为 deepseek）
    
    返回任务 ID 和状态
    """
    try:
        logger.info(f"接收到翻译请求，用户: {current_user.id}，源语言: {source_lang}，目标语言: {target_lang}")
        
        # 读取文件内容
        content = await file.read()
        content_str = content.decode("utf-8-sig")
        
        # 创建翻译作业
        job = await translation_service.create_translation_job(
            db=db,
            obj_in={
                "source_language": source_lang,
                "target_language": target_lang,
                "glossary_id": glossary_id,
                "file": content
            },
            user_id=current_user.id,
            filename=file.filename
        )
        
        # 获取术语表
        glossary = None
        if glossary_id:
            # 在实际实现中，这里应该从数据库中获取术语表
            # 为了示例，我们使用一个空字典
            glossary = {}
        
        # 使用默认引擎（如果未指定）
        if not engine:
            engine = settings.AGNO_DEFAULT_ENGINE
        
        # 在后台任务中处理翻译
        background_tasks.add_task(
            process_translation,
            db=db,
            job_id=job.id,
            content=content_str,
            source_lang=source_lang,
            target_lang=target_lang,
            glossary=glossary,
            engine=engine
        )
        
        return {
            "task_id": str(job.id),
            "status": "pending",
            "message": "翻译任务已创建，正在处理中"
        }
    
    except Exception as e:
        logger.error(f"创建翻译任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建翻译任务失败: {str(e)}")


@router.get("/status/{task_id}")
async def get_translation_status(
    task_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取翻译任务状态
    
    - **task_id**: 任务 ID
    
    返回任务状态和结果（如果可用）
    """
    try:
        # 获取翻译作业
        job = await translation_service.get(db=db, id=int(task_id))
        
        if not job:
            raise HTTPException(status_code=404, detail="翻译任务不存在")
        
        # 检查权限
        if not deps.is_superuser(current_user) and job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限查看此任务")
        
        # 构建响应
        response = {
            "task_id": str(job.id),
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "source_language": job.source_language,
            "target_language": job.target_language
        }
        
        # 添加额外信息（根据状态）
        if job.status == JobStatus.COMPLETED:
            response["download_url"] = job.download_url
            response["completed_at"] = job.completed_at.isoformat() if job.completed_at else None
            response["processing_time"] = job.processing_time
        elif job.status == JobStatus.FAILED:
            response["error_message"] = job.error_message
        
        return response
    
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务 ID")
    except Exception as e:
        logger.error(f"获取翻译任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取翻译任务状态失败: {str(e)}")


async def process_translation(
    db: AsyncSession,
    job_id: int,
    content: str,
    source_lang: str,
    target_lang: str,
    glossary: Optional[Dict[str, str]] = None,
    engine: str = "deepseek"
):
    """
    处理翻译任务（后台任务）
    
    Args:
        db: 数据库会话
        job_id: 作业 ID
        content: SRT 文件内容
        source_lang: 源语言代码
        target_lang: 目标语言代码
        glossary: 术语表
        engine: 翻译引擎
    """
    try:
        logger.info(f"开始处理翻译任务，ID: {job_id}")
        
        # 更新作业状态为处理中
        await translation_service.update_status(db=db, job_id=job_id, status=JobStatus.PROCESSING)
        
        # 调用翻译工作流
        result = await translation_workflow.process(
            content=content,
            source_lang=source_lang,
            target_lang=target_lang,
            task_id=str(job_id),
            glossary=glossary,
            engine=engine,
            chunk_size=settings.AGNO_CHUNK_SIZE
        )
        
        # 处理结果
        if result.get("status") == "completed":
            # 更新作业状态为已完成
            await translation_service.update_status(
                db=db,
                job_id=job_id,
                status=JobStatus.COMPLETED,
                download_url=result.get("download_url"),
                processing_time=result.get("processing_time", 0)
            )
            logger.info(f"翻译任务完成，ID: {job_id}")
        else:
            # 更新作业状态为失败
            await translation_service.update_status(
                db=db,
                job_id=job_id,
                status=JobStatus.FAILED,
                error_message=result.get("error", "未知错误")
            )
            logger.error(f"翻译任务失败，ID: {job_id}，错误: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"处理翻译任务过程中发生错误，ID: {job_id}，错误: {str(e)}")
        
        # 更新作业状态为失败
        await translation_service.update_status(
            db=db,
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message=str(e)
        )
