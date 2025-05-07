"""
通知服务智能体

负责生成下载 URL 和发送状态通知。
"""

import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from agno.agent import Agent
from agno.tools import tool

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("app.agents.notification")


@tool(
    name="generate_download_url",
    description="生成 SRT 文件的下载 URL",
    show_result=True
)
def generate_download_url(file_path: str, task_id: str, expiry_hours: int = 24) -> Dict[str, Any]:
    """
    生成 SRT 文件的下载 URL。
    
    Args:
        file_path: SRT 文件路径
        task_id: 任务 ID
        expiry_hours: URL 过期时间（小时），默认为 24 小时
        
    Returns:
        Dict[str, Any]: 包含下载 URL 的字典
            - download_url (str): 下载 URL
            - expiry_time (str): 过期时间
    """
    logger.info(f"生成下载 URL，任务 ID: {task_id}，文件路径: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return {
            "download_url": "",
            "expiry_time": "",
            "error": "文件不存在"
        }
    
    # 在实际实现中，这里应该生成一个真实的下载 URL
    # 可能涉及到 CDN、对象存储等服务
    # 为了示例，我们使用一个简单的模拟实现
    
    # 计算过期时间
    expiry_timestamp = int(time.time()) + expiry_hours * 3600
    expiry_time = datetime.fromtimestamp(expiry_timestamp).isoformat()
    
    # 生成下载 URL
    base_url = settings.DOWNLOAD_BASE_URL or "https://cdn.example.com/files"
    download_url = f"{base_url}/{task_id}.srt"
    
    result = {
        "download_url": download_url,
        "expiry_time": expiry_time
    }
    
    logger.info(f"下载 URL 生成成功: {download_url}，过期时间: {expiry_time}")
    
    return result


@tool(
    name="send_status_notification",
    description="发送任务状态通知",
    show_result=True
)
def send_status_notification(
    task_id: str,
    status: str,
    download_url: Optional[str] = None,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    发送任务状态通知。
    
    Args:
        task_id: 任务 ID
        status: 任务状态，可选值为 "completed"、"failed" 或 "processing"
        download_url: 下载 URL，仅在状态为 "completed" 时有效
        error_message: 错误消息，仅在状态为 "failed" 时有效
        
    Returns:
        Dict[str, Any]: 包含通知结果的字典
            - success (bool): 是否成功
            - message (str): 消息
    """
    logger.info(f"发送状态通知，任务 ID: {task_id}，状态: {status}")
    
    # 在实际实现中，这里应该发送真实的通知
    # 可能涉及到 WebSocket、邮件、短信等通知渠道
    # 为了示例，我们使用一个简单的模拟实现
    
    notification_message = ""
    
    if status == "completed":
        notification_message = f"任务 {task_id} 已完成，下载 URL: {download_url}"
    elif status == "failed":
        notification_message = f"任务 {task_id} 失败，错误: {error_message}"
    elif status == "processing":
        notification_message = f"任务 {task_id} 正在处理中"
    else:
        notification_message = f"任务 {task_id} 状态更新: {status}"
    
    result = {
        "success": True,
        "message": notification_message
    }
    
    logger.info(f"状态通知发送成功: {notification_message}")
    
    return result


class NotificationAgent:
    """通知服务智能体，负责生成下载 URL 和发送状态通知"""
    
    def __init__(self):
        """初始化通知服务智能体"""
        # 使用配置的模型
        engine = settings.AGNO_NOTIFICATION_ENGINE
        logger.info(f"初始化通知服务智能体，使用模型: {engine}")
        
        self.agent = Agent(
            tools=[generate_download_url, send_status_notification],
            instructions=[
                "你是一个专业的通知服务助手",
                "你的任务是生成下载 URL 和发送状态通知",
                "只在需要时调用工具，不要主动调用"
            ],
            markdown=True,
            model=engine
        )
    
    async def generate_url(
        self,
        file_path: str,
        task_id: str,
        expiry_hours: int = 24
    ) -> Dict[str, Any]:
        """
        生成下载 URL
        
        Args:
            file_path: SRT 文件路径
            task_id: 任务 ID
            expiry_hours: URL 过期时间（小时）
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            # 直接调用工具函数，而不是通过 agent 处理
            result = generate_download_url(file_path, task_id, expiry_hours)
            return result
        except Exception as e:
            logger.error(f"生成下载 URL 过程中发生错误: {str(e)}")
            return {
                "download_url": "",
                "expiry_time": "",
                "error": f"生成下载 URL 过程中发生错误: {str(e)}"
            }
    
    async def send_notification(
        self,
        task_id: str,
        status: str,
        download_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送状态通知
        
        Args:
            task_id: 任务 ID
            status: 任务状态
            download_url: 下载 URL
            error_message: 错误消息
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            # 直接调用工具函数，而不是通过 agent 处理
            result = send_status_notification(task_id, status, download_url, error_message)
            return result
        except Exception as e:
            logger.error(f"发送状态通知过程中发生错误: {str(e)}")
            return {
                "success": False,
                "message": f"发送状态通知过程中发生错误: {str(e)}"
            }
