"""
SRT 重组智能体测试

测试 SRT 重组智能体的功能，包括重组翻译后的 SRT 块和确保字幕 ID 连续性。
"""

import pytest
from app.agents.srt_reassembler import reassemble_srt, SRTReassemblerAgent
from app.core.config import settings


# 测试用 SRT 块
TEST_SRT_CHUNKS = [
    {
        "id": 1,
        "content": """1
00:00:01,000 --> 00:00:04,000
你好世界

2
00:00:05,000 --> 00:00:09,000
这是一个测试
""",
        "subtitle_range": {"start": 1, "end": 2}
    },
    {
        "id": 2,
        "content": """3
00:00:10,000 --> 00:00:14,000
第三个字幕

4
00:00:15,000 --> 00:00:19,000
第四个字幕
""",
        "subtitle_range": {"start": 3, "end": 4}
    }
]

# 测试用 SRT 块 - ID 不连续
TEST_SRT_CHUNKS_DISCONTINUOUS = [
    {
        "id": 1,
        "content": """1
00:00:01,000 --> 00:00:04,000
你好世界

5
00:00:05,000 --> 00:00:09,000
这是一个测试
""",
        "subtitle_range": {"start": 1, "end": 5}
    },
    {
        "id": 2,
        "content": """10
00:00:10,000 --> 00:00:14,000
第三个字幕

15
00:00:15,000 --> 00:00:19,000
第四个字幕
""",
        "subtitle_range": {"start": 10, "end": 15}
    }
]

# 测试用 SRT 块 - 包含多行文本
TEST_SRT_CHUNKS_MULTILINE = [
    {
        "id": 1,
        "content": """1
00:00:01,000 --> 00:00:04,000
你好世界
这是多行文本

2
00:00:05,000 --> 00:00:09,000
这是一个测试
""",
        "subtitle_range": {"start": 1, "end": 2}
    },
    {
        "id": 2,
        "content": """3
00:00:10,000 --> 00:00:14,000
第三个字幕
包含
多行
文本

4
00:00:15,000 --> 00:00:19,000
第四个字幕
""",
        "subtitle_range": {"start": 3, "end": 4}
    }
]


def test_reassemble_srt_basic():
    """测试基本的 SRT 重组功能"""
    result = reassemble_srt(TEST_SRT_CHUNKS)
    
    assert "content" in result
    assert "subtitle_count" in result
    assert result["subtitle_count"] == 4
    
    # 验证内容
    content = result["content"]
    assert "1\n00:00:01,000 --> 00:00:04,000\n你好世界" in content
    assert "2\n00:00:05,000 --> 00:00:09,000\n这是一个测试" in content
    assert "3\n00:00:10,000 --> 00:00:14,000\n第三个字幕" in content
    assert "4\n00:00:15,000 --> 00:00:19,000\n第四个字幕" in content


def test_reassemble_srt_normalize_ids():
    """测试重组时规范化字幕 ID"""
    result = reassemble_srt(TEST_SRT_CHUNKS_DISCONTINUOUS, normalize_ids=True)
    
    assert result["subtitle_count"] == 4
    
    # 验证 ID 已规范化
    content = result["content"]
    assert "1\n00:00:01,000 --> 00:00:04,000\n你好世界" in content
    assert "2\n00:00:05,000 --> 00:00:09,000\n这是一个测试" in content
    assert "3\n00:00:10,000 --> 00:00:14,000\n第三个字幕" in content
    assert "4\n00:00:15,000 --> 00:00:19,000\n第四个字幕" in content


def test_reassemble_srt_keep_original_ids():
    """测试重组时保留原始字幕 ID"""
    result = reassemble_srt(TEST_SRT_CHUNKS_DISCONTINUOUS, normalize_ids=False)
    
    assert result["subtitle_count"] == 4
    
    # 验证保留了原始 ID
    content = result["content"]
    assert "1\n00:00:01,000 --> 00:00:04,000\n你好世界" in content
    assert "5\n00:00:05,000 --> 00:00:09,000\n这是一个测试" in content
    assert "10\n00:00:10,000 --> 00:00:14,000\n第三个字幕" in content
    assert "15\n00:00:15,000 --> 00:00:19,000\n第四个字幕" in content


def test_reassemble_srt_multiline():
    """测试重组包含多行文本的 SRT 块"""
    result = reassemble_srt(TEST_SRT_CHUNKS_MULTILINE)
    
    assert result["subtitle_count"] == 4
    
    # 验证多行文本
    content = result["content"]
    assert "1\n00:00:01,000 --> 00:00:04,000\n你好世界\n这是多行文本" in content
    assert "3\n00:00:10,000 --> 00:00:14,000\n第三个字幕\n包含\n多行\n文本" in content


def test_reassemble_srt_empty():
    """测试重组空的 SRT 块"""
    result = reassemble_srt([])
    
    assert result["subtitle_count"] == 0
    assert result["content"] == ""


def test_reassemble_srt_single_chunk():
    """测试重组单个 SRT 块"""
    result = reassemble_srt([TEST_SRT_CHUNKS[0]])
    
    assert result["subtitle_count"] == 2
    assert "1\n00:00:01,000 --> 00:00:04,000\n你好世界" in result["content"]
    assert "2\n00:00:05,000 --> 00:00:09,000\n这是一个测试" in result["content"]


@pytest.mark.asyncio
async def test_srt_reassembler_agent():
    """测试 SRT 重组智能体"""
    # 确保使用 Mistral 模型
    original_engine = settings.AGNO_REASSEMBLER_ENGINE
    settings.AGNO_REASSEMBLER_ENGINE = "mistral"
    
    # 创建智能体
    reassembler = SRTReassemblerAgent()
    
    # 重组 SRT 块
    result = await reassembler.reassemble(TEST_SRT_CHUNKS)
    
    assert "content" in result
    assert "subtitle_count" in result
    assert result["subtitle_count"] == 4
    
    # 验证内容
    content = result["content"]
    assert "1\n00:00:01,000 --> 00:00:04,000\n你好世界" in content
    assert "4\n00:00:15,000 --> 00:00:19,000\n第四个字幕" in content
    
    # 恢复原始设置
    settings.AGNO_REASSEMBLER_ENGINE = original_engine
