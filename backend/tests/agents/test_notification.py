"""
通知智能体测试

测试通知智能体的功能，包括生成下载 URL 和发送状态通知。
"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.agents.notification import generate_download_url, NotificationAgent
from app.core.config import settings


def test_generate_download_url():
    """测试生成下载 URL 功能"""
    # 测试文件路径和任务 ID
    file_path = "/tmp/test_file.srt"
    task_id = "test_task_123"
    expiry_hours = 24
    
    # 确保测试文件存在
    with open(file_path, "w") as f:
        f.write("测试内容")
    
    try:
        # 生成下载 URL
        result = generate_download_url(file_path, task_id, expiry_hours)
        
        # 验证结果
        assert "download_url" in result
        assert "expiry_time" in result
        
        # 验证下载 URL 包含任务 ID
        assert task_id in result["download_url"]
        
        # 验证过期时间
        now = datetime.now()
        expiry = datetime.fromisoformat(result["expiry_time"])
        time_diff = expiry - now
        
        # 允许有几秒钟的误差
        assert abs(time_diff.total_seconds() - expiry_hours * 3600) < 10
    finally:
        # 清理测试文件
        if os.path.exists(file_path):
            os.remove(file_path)


@pytest.mark.asyncio
async def test_notification_agent_download_url():
    """测试通知智能体生成下载 URL 功能"""
    # 确保使用 Mistral 模型
    original_engine = settings.AGNO_NOTIFICATION_ENGINE
    settings.AGNO_NOTIFICATION_ENGINE = "mistral"
    
    # 创建智能体
    agent = NotificationAgent()
    
    # 测试文件路径和任务 ID
    file_path = "/tmp/test_agent_file.srt"
    task_id = "test_agent_task_456"
    
    # 确保测试文件存在
    with open(file_path, "w") as f:
        f.write("测试内容")
    
    try:
        # 生成下载 URL
        result = await agent.generate_download_url(file_path, task_id)
        
        # 验证结果
        assert "download_url" in result
        assert "expiry_time" in result
        assert task_id in result["download_url"]
    finally:
        # 清理测试文件
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 恢复原始设置
        settings.AGNO_NOTIFICATION_ENGINE = original_engine


@pytest.mark.asyncio
async def test_notification_agent_send_status():
    """测试通知智能体发送状态通知功能"""
    # 确保使用 Mistral 模型
    original_engine = settings.AGNO_NOTIFICATION_ENGINE
    settings.AGNO_NOTIFICATION_ENGINE = "mistral"
    
    # 创建智能体
    agent = NotificationAgent()
    
    # 模拟数据库会话和用户服务
    mock_db = MagicMock()
    mock_user_service = MagicMock()
    
    # 模拟用户数据
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    
    # 设置模拟用户服务返回模拟用户
    mock_user_service.get.return_value = mock_user
    
    # 使用模拟对象替代实际发送邮件功能
    with patch('app.agents.notification.send_email') as mock_send_email:
        # 发送状态通知
        result = await agent.send_status(
            db=mock_db,
            user_service=mock_user_service,
            user_id=1,
            task_id="test_status_task_789",
            status="completed",
            download_url="http://example.com/download/test_status_task_789",
            error_message=None
        )
        
        # 验证结果
        assert result["success"] is True
        assert "message" in result
        
        # 验证调用了发送邮件函数
        mock_send_email.assert_called_once()
        
        # 验证发送邮件的参数
        call_args = mock_send_email.call_args[1]
        assert call_args["email_to"] == mock_user.email
        assert "completed" in call_args["subject"]
        assert "http://example.com/download/test_status_task_789" in call_args["html_content"]
    
    # 恢复原始设置
    settings.AGNO_NOTIFICATION_ENGINE = original_engine


@pytest.mark.asyncio
async def test_notification_agent_send_error_status():
    """测试通知智能体发送错误状态通知功能"""
    # 确保使用 Mistral 模型
    original_engine = settings.AGNO_NOTIFICATION_ENGINE
    settings.AGNO_NOTIFICATION_ENGINE = "mistral"
    
    # 创建智能体
    agent = NotificationAgent()
    
    # 模拟数据库会话和用户服务
    mock_db = MagicMock()
    mock_user_service = MagicMock()
    
    # 模拟用户数据
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    
    # 设置模拟用户服务返回模拟用户
    mock_user_service.get.return_value = mock_user
    
    # 使用模拟对象替代实际发送邮件功能
    with patch('app.agents.notification.send_email') as mock_send_email:
        # 发送错误状态通知
        error_message = "翻译过程中出现错误：无效的 SRT 格式"
        
        result = await agent.send_status(
            db=mock_db,
            user_service=mock_user_service,
            user_id=1,
            task_id="test_error_task_789",
            status="failed",
            download_url=None,
            error_message=error_message
        )
        
        # 验证结果
        assert result["success"] is True
        assert "message" in result
        
        # 验证调用了发送邮件函数
        mock_send_email.assert_called_once()
        
        # 验证发送邮件的参数
        call_args = mock_send_email.call_args[1]
        assert call_args["email_to"] == mock_user.email
        assert "failed" in call_args["subject"]
        assert error_message in call_args["html_content"]
    
    # 恢复原始设置
    settings.AGNO_NOTIFICATION_ENGINE = original_engine
