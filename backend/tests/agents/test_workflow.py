"""
翻译工作流测试

测试翻译工作流的功能，包括整个翻译流程的协调和各个智能体的集成。
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from app.agents.workflow import TranslationWorkflow
from app.core.config import settings


# 有效的 SRT 内容
VALID_SRT = """1
00:00:01,000 --> 00:00:04,000
Hello world

2
00:00:05,000 --> 00:00:09,000
This is a test
"""

# 测试用术语表
TEST_GLOSSARY = {
    "Hello": "你好",
    "world": "世界",
    "test": "测试"
}


@pytest.mark.asyncio
async def test_workflow_process():
    """测试翻译工作流的完整处理过程"""
    # 保存原始设置
    original_settings = {
        "validator_engine": settings.AGNO_VALIDATOR_ENGINE,
        "splitter_engine": settings.AGNO_SPLITTER_ENGINE,
        "translator_engine": settings.AGNO_TRANSLATOR_ENGINE,
        "reassembler_engine": settings.AGNO_REASSEMBLER_ENGINE,
        "notification_engine": settings.AGNO_NOTIFICATION_ENGINE,
        "default_engine": settings.AGNO_DEFAULT_ENGINE
    }
    
    # 设置所有智能体使用 Mistral 引擎
    settings.AGNO_VALIDATOR_ENGINE = "mistral"
    settings.AGNO_SPLITTER_ENGINE = "mistral"
    settings.AGNO_TRANSLATOR_ENGINE = "mistral"
    settings.AGNO_REASSEMBLER_ENGINE = "mistral"
    settings.AGNO_NOTIFICATION_ENGINE = "mistral"
    settings.AGNO_DEFAULT_ENGINE = "mistral"
    
    # 创建临时输出文件
    output_file = "/tmp/test_workflow_output.srt"
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # 模拟各个智能体的方法
    with patch('app.agents.srt_validator.SRTValidatorAgent.validate') as mock_validate, \
         patch('app.agents.srt_splitter.SRTSplitterAgent.split') as mock_split, \
         patch('app.agents.translator.TranslatorAgent.translate') as mock_translate, \
         patch('app.agents.srt_reassembler.SRTReassemblerAgent.reassemble') as mock_reassemble, \
         patch('app.agents.notification.NotificationAgent.generate_download_url') as mock_generate_url:
        
        # 设置模拟方法的返回值
        mock_validate.return_value = {"valid": True, "errors": []}
        
        mock_split.return_value = {
            "chunks": [
                {
                    "id": 1,
                    "content": VALID_SRT,
                    "subtitle_range": {"start": 1, "end": 2}
                }
            ],
            "total_subtitles": 2
        }
        
        mock_translate.return_value = {
            "translated_content": """1
00:00:01,000 --> 00:00:04,000
你好世界

2
00:00:05,000 --> 00:00:09,000
这是一个测试
""",
            "engine": "mistral",
            "glossary_matches": ["Hello", "world", "test"]
        }
        
        mock_reassemble.return_value = {
            "content": """1
00:00:01,000 --> 00:00:04,000
你好世界

2
00:00:05,000 --> 00:00:09,000
这是一个测试
""",
            "subtitle_count": 2
        }
        
        mock_generate_url.return_value = {
            "download_url": "http://example.com/download/test_task_123",
            "expiry_time": "2023-12-31T23:59:59"
        }
        
        # 创建工作流
        workflow = TranslationWorkflow()
        
        # 处理翻译任务
        result = await workflow.process(
            content=VALID_SRT,
            source_lang="en",
            target_lang="zh",
            task_id="test_task_123",
            glossary=TEST_GLOSSARY,
            engine="mistral",
            chunk_size=100
        )
        
        # 验证结果
        assert result["task_id"] == "test_task_123"
        assert result["status"] == "completed"
        assert result["download_url"] == "http://example.com/download/test_task_123"
        
        # 验证调用了各个智能体的方法
        mock_validate.assert_called_once()
        mock_split.assert_called_once()
        mock_translate.assert_called_once()
        mock_reassemble.assert_called_once()
        mock_generate_url.assert_called_once()
    
    # 恢复原始设置
    settings.AGNO_VALIDATOR_ENGINE = original_settings["validator_engine"]
    settings.AGNO_SPLITTER_ENGINE = original_settings["splitter_engine"]
    settings.AGNO_TRANSLATOR_ENGINE = original_settings["translator_engine"]
    settings.AGNO_REASSEMBLER_ENGINE = original_settings["reassembler_engine"]
    settings.AGNO_NOTIFICATION_ENGINE = original_settings["notification_engine"]
    settings.AGNO_DEFAULT_ENGINE = original_settings["default_engine"]


@pytest.mark.asyncio
async def test_workflow_validation_error():
    """测试翻译工作流处理验证错误的情况"""
    # 设置所有智能体使用 Mistral 引擎
    settings.AGNO_VALIDATOR_ENGINE = "mistral"
    settings.AGNO_DEFAULT_ENGINE = "mistral"
    
    # 模拟验证智能体返回错误
    with patch('app.agents.srt_validator.SRTValidatorAgent.validate') as mock_validate:
        # 设置模拟方法返回验证错误
        mock_validate.return_value = {
            "valid": False,
            "errors": [
                {"line": 2, "error": "无效的时间格式"}
            ]
        }
        
        # 创建工作流
        workflow = TranslationWorkflow()
        
        # 处理翻译任务
        result = await workflow.process(
            content="无效的 SRT 内容",
            source_lang="en",
            target_lang="zh",
            task_id="test_error_task"
        )
        
        # 验证结果
        assert result["task_id"] == "test_error_task"
        assert result["status"] == "failed"
        assert "error" in result
        assert "无效的时间格式" in result["error"]


@pytest.mark.asyncio
async def test_workflow_translation_error():
    """测试翻译工作流处理翻译错误的情况"""
    # 设置所有智能体使用 Mistral 引擎
    settings.AGNO_VALIDATOR_ENGINE = "mistral"
    settings.AGNO_SPLITTER_ENGINE = "mistral"
    settings.AGNO_TRANSLATOR_ENGINE = "mistral"
    settings.AGNO_DEFAULT_ENGINE = "mistral"
    
    # 模拟验证和分割成功，但翻译失败
    with patch('app.agents.srt_validator.SRTValidatorAgent.validate') as mock_validate, \
         patch('app.agents.srt_splitter.SRTSplitterAgent.split') as mock_split, \
         patch('app.agents.translator.TranslatorAgent.translate') as mock_translate:
        
        # 设置模拟方法的返回值
        mock_validate.return_value = {"valid": True, "errors": []}
        
        mock_split.return_value = {
            "chunks": [
                {
                    "id": 1,
                    "content": VALID_SRT,
                    "subtitle_range": {"start": 1, "end": 2}
                }
            ],
            "total_subtitles": 2
        }
        
        # 模拟翻译失败
        mock_translate.side_effect = Exception("翻译服务暂时不可用")
        
        # 创建工作流
        workflow = TranslationWorkflow()
        
        # 处理翻译任务
        result = await workflow.process(
            content=VALID_SRT,
            source_lang="en",
            target_lang="zh",
            task_id="test_translation_error_task"
        )
        
        # 验证结果
        assert result["task_id"] == "test_translation_error_task"
        assert result["status"] == "failed"
        assert "error" in result
        assert "翻译服务暂时不可用" in result["error"]


@pytest.mark.asyncio
async def test_workflow_with_different_engines():
    """测试翻译工作流使用不同引擎的情况"""
    # 保存原始设置
    original_settings = {
        "validator_engine": settings.AGNO_VALIDATOR_ENGINE,
        "splitter_engine": settings.AGNO_SPLITTER_ENGINE,
        "translator_engine": settings.AGNO_TRANSLATOR_ENGINE,
        "reassembler_engine": settings.AGNO_REASSEMBLER_ENGINE,
        "notification_engine": settings.AGNO_NOTIFICATION_ENGINE,
        "default_engine": settings.AGNO_DEFAULT_ENGINE
    }
    
    # 设置不同的引擎
    settings.AGNO_VALIDATOR_ENGINE = "mistral"
    settings.AGNO_SPLITTER_ENGINE = "mistral"
    settings.AGNO_TRANSLATOR_ENGINE = "deepseek"  # 翻译使用 DeepSeek
    settings.AGNO_REASSEMBLER_ENGINE = "mistral"
    settings.AGNO_NOTIFICATION_ENGINE = "mistral"
    settings.AGNO_DEFAULT_ENGINE = "mistral"
    
    # 模拟各个智能体的方法
    with patch('app.agents.srt_validator.SRTValidatorAgent.validate') as mock_validate, \
         patch('app.agents.srt_splitter.SRTSplitterAgent.split') as mock_split, \
         patch('app.agents.translator.TranslatorAgent.translate') as mock_translate, \
         patch('app.agents.srt_reassembler.SRTReassemblerAgent.reassemble') as mock_reassemble, \
         patch('app.agents.notification.NotificationAgent.generate_download_url') as mock_generate_url, \
         patch('app.agents.translator.settings.DEEPSEEK_API_KEY', 'fake_key'):
        
        # 设置模拟方法的返回值
        mock_validate.return_value = {"valid": True, "errors": []}
        
        mock_split.return_value = {
            "chunks": [
                {
                    "id": 1,
                    "content": VALID_SRT,
                    "subtitle_range": {"start": 1, "end": 2}
                }
            ],
            "total_subtitles": 2
        }
        
        mock_translate.return_value = {
            "translated_content": "翻译内容",
            "engine": "deepseek",  # 使用 DeepSeek 引擎
            "glossary_matches": ["Hello", "world", "test"]
        }
        
        mock_reassemble.return_value = {
            "content": "重组后的内容",
            "subtitle_count": 2
        }
        
        mock_generate_url.return_value = {
            "download_url": "http://example.com/download/test_engines_task",
            "expiry_time": "2023-12-31T23:59:59"
        }
        
        # 创建工作流
        workflow = TranslationWorkflow()
        
        # 处理翻译任务，不指定引擎，应该使用配置的 DeepSeek
        result = await workflow.process(
            content=VALID_SRT,
            source_lang="en",
            target_lang="zh",
            task_id="test_engines_task",
            glossary=TEST_GLOSSARY
        )
        
        # 验证结果
        assert result["task_id"] == "test_engines_task"
        assert result["status"] == "completed"
        
        # 验证调用翻译智能体时使用了 DeepSeek 引擎
        mock_translate.assert_called_once()
        call_args = mock_translate.call_args[1]
        assert call_args.get("engine") == "deepseek"
    
    # 恢复原始设置
    settings.AGNO_VALIDATOR_ENGINE = original_settings["validator_engine"]
    settings.AGNO_SPLITTER_ENGINE = original_settings["splitter_engine"]
    settings.AGNO_TRANSLATOR_ENGINE = original_settings["translator_engine"]
    settings.AGNO_REASSEMBLER_ENGINE = original_settings["reassembler_engine"]
    settings.AGNO_NOTIFICATION_ENGINE = original_settings["notification_engine"]
    settings.AGNO_DEFAULT_ENGINE = original_settings["default_engine"]
