"""
翻译工作流管理器

负责协调各个智能体的工作流程，并提供一个统一的接口供 API 调用。
"""

import os
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Tuple

from app.core.logging import get_logger
from app.core.config import settings
from app.agents.srt_validator import SRTValidatorAgent
from app.agents.srt_splitter import SRTSplitterAgent
from app.agents.translator import TranslatorAgent
from app.agents.srt_reassembler import SRTReassemblerAgent
from app.agents.notification import NotificationAgent

logger = get_logger("app.agents.workflow")


class TranslationWorkflow:
    """翻译工作流管理器，协调各个智能体的工作流程"""
    
    def __init__(self):
        """初始化翻译工作流管理器"""
        logger.info("初始化翻译工作流管理器")
        
        # 初始化智能体
        self.validator = SRTValidatorAgent()
        self.splitter = SRTSplitterAgent()
        self.translator = TranslatorAgent()
        self.reassembler = SRTReassemblerAgent()
        self.notification = NotificationAgent()
        
        # 确保数据目录存在
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.CHUNKS_DIR, exist_ok=True)
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    
    async def process(
        self,
        content: str,
        source_lang: str,
        target_lang: str,
        task_id: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
        engine: Optional[str] = None,
        chunk_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        处理翻译任务
        
        Args:
            content: SRT 文件内容
            source_lang: 源语言代码
            target_lang: 目标语言代码
            task_id: 任务 ID，如果为 None 则自动生成
            glossary: 术语表
            engine: 翻译引擎
            chunk_size: 分块大小
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 生成任务 ID
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # 使用默认引擎（如果未指定）
        if engine is None:
            engine = settings.AGNO_DEFAULT_ENGINE
        
        # 使用默认分块大小（如果未指定）
        if chunk_size is None:
            chunk_size = settings.AGNO_CHUNK_SIZE
        
        logger.info(f"开始处理翻译任务，ID: {task_id}，源语言: {source_lang}，目标语言: {target_lang}，引擎: {engine}，分块大小: {chunk_size}")
        
        try:
            # 1. 验证 SRT 文件格式
            validation_result = await self.validator.validate(content)
            
            if not validation_result.get("valid", False):
                logger.error(f"SRT 文件格式验证失败: {validation_result.get('errors')}")
                
                # 发送失败通知
                await self.notification.send_notification(
                    task_id=task_id,
                    status="failed",
                    error_message="SRT 文件格式验证失败"
                )
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "SRT 文件格式验证失败",
                    "details": validation_result
                }
            
            # 2. 分块处理
            splitting_result = await self.splitter.split(content, chunk_size)
            
            if "error" in splitting_result:
                logger.error(f"SRT 文件分块失败: {splitting_result.get('error')}")
                
                # 发送失败通知
                await self.notification.send_notification(
                    task_id=task_id,
                    status="failed",
                    error_message="SRT 文件分块失败"
                )
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "SRT 文件分块失败",
                    "details": splitting_result
                }
            
            # 3. 翻译每个块
            chunks = splitting_result.get("chunks", [])
            translated_chunks = []
            
            # 发送处理中通知
            await self.notification.send_notification(
                task_id=task_id,
                status="processing"
            )
            
            # 并行翻译所有块
            translation_tasks = []
            for chunk in chunks:
                task = self.translator.translate(
                    content=chunk.get("content", ""),
                    source_lang=source_lang,
                    target_lang=target_lang,
                    glossary=glossary,
                    engine=engine
                )
                translation_tasks.append(task)
            
            # 等待所有翻译任务完成
            translation_results = await asyncio.gather(*translation_tasks)
            
            # 检查翻译结果
            for i, result in enumerate(translation_results):
                if "error" in result:
                    logger.error(f"块 {i+1} 翻译失败: {result.get('error')}")
                    continue
                
                translated_chunks.append({
                    "id": chunks[i].get("id"),
                    "translated_content": result.get("translated_content", "")
                })
            
            # 如果没有成功翻译的块，返回错误
            if not translated_chunks:
                logger.error("所有块翻译失败")
                
                # 发送失败通知
                await self.notification.send_notification(
                    task_id=task_id,
                    status="failed",
                    error_message="所有块翻译失败"
                )
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "所有块翻译失败",
                    "details": translation_results
                }
            
            # 4. 重组翻译后的内容
            reassembly_result = await self.reassembler.reassemble(translated_chunks)
            
            if "error" in reassembly_result:
                logger.error(f"SRT 文件重组失败: {reassembly_result.get('error')}")
                
                # 发送失败通知
                await self.notification.send_notification(
                    task_id=task_id,
                    status="failed",
                    error_message="SRT 文件重组失败"
                )
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "SRT 文件重组失败",
                    "details": reassembly_result
                }
            
            # 5. 保存结果
            content = reassembly_result.get("content", "")
            save_result = await self.reassembler.save_file(content, task_id)
            
            if "error" in save_result:
                logger.error(f"SRT 文件保存失败: {save_result.get('error')}")
                
                # 发送失败通知
                await self.notification.send_notification(
                    task_id=task_id,
                    status="failed",
                    error_message="SRT 文件保存失败"
                )
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "SRT 文件保存失败",
                    "details": save_result
                }
            
            # 6. 生成下载 URL
            file_path = save_result.get("file_path", "")
            url_result = await self.notification.generate_url(file_path, task_id)
            
            if "error" in url_result:
                logger.error(f"下载 URL 生成失败: {url_result.get('error')}")
                
                # 发送失败通知
                await self.notification.send_notification(
                    task_id=task_id,
                    status="failed",
                    error_message="下载 URL 生成失败"
                )
                
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "下载 URL 生成失败",
                    "details": url_result
                }
            
            # 7. 发送完成通知
            download_url = url_result.get("download_url", "")
            await self.notification.send_notification(
                task_id=task_id,
                status="completed",
                download_url=download_url
            )
            
            # 8. 返回结果
            return {
                "task_id": task_id,
                "status": "completed",
                "download_url": download_url,
                "subtitle_count": reassembly_result.get("subtitle_count", 0),
                "file_size": save_result.get("file_size", 0),
                "expiry_time": url_result.get("expiry_time", "")
            }
        
        except Exception as e:
            logger.error(f"翻译任务处理过程中发生错误: {str(e)}")
            
            # 发送失败通知
            await self.notification.send_notification(
                task_id=task_id,
                status="failed",
                error_message=str(e)
            )
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"处理过程中发生错误: {str(e)}"
            }


# 创建工作流管理器实例
translation_workflow = TranslationWorkflow()
