"""
翻译智能体测试

测试翻译智能体的功能，包括使用不同的翻译引擎和术语表替换。
"""

import pytest
from unittest.mock import patch
from app.agents.translator import translate_chunk, TranslatorAgent, _translate_with_deepseek, _translate_with_mistral
from app.core.config import settings


# 测试用 SRT 块内容
TEST_SRT_CHUNK = """1
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


def test_translate_chunk_with_deepseek():
    """测试使用 DeepSeek 引擎翻译 SRT 块"""
    # 模拟 DeepSeek API 密钥存在
    with patch('app.agents.translator.settings.DEEPSEEK_API_KEY', 'fake_key'):
        result = translate_chunk(
            content=TEST_SRT_CHUNK,
            source_lang="en",
            target_lang="zh",
            glossary=TEST_GLOSSARY,
            engine="deepseek"
        )
        
        assert "translated_content" in result
        assert "engine" in result
        assert "glossary_matches" in result
        assert result["engine"] == "deepseek"
        
        # 验证术语表替换
        assert len(result["glossary_matches"]) > 0
        assert "你好" in result["translated_content"]
        assert "世界" in result["translated_content"]


def test_translate_chunk_with_mistral():
    """测试使用 Mistral 引擎翻译 SRT 块"""
    result = translate_chunk(
        content=TEST_SRT_CHUNK,
        source_lang="en",
        target_lang="zh",
        glossary=TEST_GLOSSARY,
        engine="mistral"
    )
    
    assert "translated_content" in result
    assert "engine" in result
    assert "glossary_matches" in result
    assert result["engine"] == "mistral"
    
    # 验证术语表替换
    assert len(result["glossary_matches"]) > 0
    assert "你好" in result["translated_content"]
    assert "世界" in result["translated_content"]


def test_translate_chunk_fallback():
    """测试当指定引擎不可用时的回退机制"""
    # 使用不存在的引擎，应该回退到 DeepSeek
    with patch('app.agents.translator.settings.DEEPSEEK_API_KEY', 'fake_key'):
        with patch('app.agents.translator.logger') as mock_logger:
            result = translate_chunk(
                content=TEST_SRT_CHUNK,
                source_lang="en",
                target_lang="zh",
                glossary=None,
                engine="nonexistent_engine"
            )
            
            # 验证记录了警告日志
            mock_logger.warning.assert_called()
            
            # 验证回退到了 DeepSeek
            assert result["engine"] == "deepseek"


def test_translate_with_deepseek():
    """测试 DeepSeek 翻译函数"""
    text = "Hello world, this is a test."
    result = _translate_with_deepseek(
        text=text,
        source_lang="en",
        target_lang="zh",
        glossary=TEST_GLOSSARY
    )
    
    # 验证结果包含源语言和目标语言
    assert "[en -> zh]" in result
    
    # 验证术语表替换
    assert "你好" in result
    assert "世界" in result
    assert "测试" in result


def test_translate_with_mistral():
    """测试 Mistral 翻译函数"""
    text = "Hello world, this is a test."
    result = _translate_with_mistral(
        text=text,
        source_lang="en",
        target_lang="zh",
        glossary=TEST_GLOSSARY
    )
    
    # 验证结果包含源语言和目标语言
    assert "[Mistral: en -> zh]" in result
    
    # 验证术语表替换
    assert "你好" in result
    assert "世界" in result
    assert "测试" in result


@pytest.mark.asyncio
async def test_translator_agent_default_engine():
    """测试翻译智能体使用默认引擎"""
    # 保存原始设置
    original_translator_engine = settings.AGNO_TRANSLATOR_ENGINE
    original_default_engine = settings.AGNO_DEFAULT_ENGINE
    
    # 设置 Mistral 为默认引擎
    settings.AGNO_TRANSLATOR_ENGINE = "mistral"
    settings.AGNO_DEFAULT_ENGINE = "mistral"
    
    # 创建智能体
    translator = TranslatorAgent()
    
    # 翻译内容
    result = await translator.translate(
        content=TEST_SRT_CHUNK,
        source_lang="en",
        target_lang="zh",
        glossary=TEST_GLOSSARY
    )
    
    # 验证使用了默认引擎 (Mistral)
    assert result["engine"] == "mistral"
    
    # 恢复原始设置
    settings.AGNO_TRANSLATOR_ENGINE = original_translator_engine
    settings.AGNO_DEFAULT_ENGINE = original_default_engine


@pytest.mark.asyncio
async def test_translator_agent_specified_engine():
    """测试翻译智能体使用指定引擎"""
    # 保存原始设置
    original_translator_engine = settings.AGNO_TRANSLATOR_ENGINE
    original_default_engine = settings.AGNO_DEFAULT_ENGINE
    
    # 设置 Mistral 为默认引擎
    settings.AGNO_TRANSLATOR_ENGINE = "mistral"
    settings.AGNO_DEFAULT_ENGINE = "mistral"
    
    # 创建智能体
    translator = TranslatorAgent()
    
    # 翻译内容，指定使用 DeepSeek 引擎
    with patch('app.agents.translator.settings.DEEPSEEK_API_KEY', 'fake_key'):
        result = await translator.translate(
            content=TEST_SRT_CHUNK,
            source_lang="en",
            target_lang="zh",
            glossary=TEST_GLOSSARY,
            engine="deepseek"
        )
        
        # 验证使用了指定引擎 (DeepSeek)
        assert result["engine"] == "deepseek"
    
    # 恢复原始设置
    settings.AGNO_TRANSLATOR_ENGINE = original_translator_engine
    settings.AGNO_DEFAULT_ENGINE = original_default_engine
