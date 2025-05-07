"""
SRT 分割智能体测试

测试 SRT 分割智能体的功能，包括分割 SRT 文件和确保不会在字幕中间拆分。
"""

import pytest
from app.agents.srt_splitter import split_srt, SRTSplitterAgent
from app.core.config import settings


# 测试用 SRT 内容
TEST_SRT = """1
00:00:01,000 --> 00:00:04,000
这是第一条字幕

2
00:00:05,000 --> 00:00:09,000
这是第二条字幕

3
00:00:10,000 --> 00:00:14,000
这是第三条字幕
多行文本

4
00:00:15,000 --> 00:00:19,000
这是第四条字幕

5
00:00:20,000 --> 00:00:24,000
这是第五条字幕
"""

# 复杂格式的 SRT 内容，包含多行文本和特殊字符
COMPLEX_SRT = """1
00:00:01,000 --> 00:00:04,000
这是第一条字幕
包含多行文本
和特殊字符：!@#$%^&*()

2
00:00:05,000 --> 00:00:09,000
这是第二条字幕
- 包含对话格式
- 和列表形式

3
00:00:10,000 --> 00:00:14,000
<i>这是斜体文本</i>
<b>这是粗体文本</b>
"""

# 不规范的 SRT 内容，缺少空行
IRREGULAR_SRT = """1
00:00:01,000 --> 00:00:04,000
这是第一条字幕
2
00:00:05,000 --> 00:00:09,000
这是第二条字幕
3
00:00:10,000 --> 00:00:14,000
这是第三条字幕"""


def test_split_srt_basic():
    """测试基本的 SRT 分割功能"""
    result = split_srt(TEST_SRT, chunk_size=2)
    
    assert "chunks" in result
    assert "total_subtitles" in result
    assert result["total_subtitles"] == 5
    assert len(result["chunks"]) == 3  # 5个字幕，每块2个，应该有3个块
    
    # 验证第一个块
    assert result["chunks"][0]["id"] == 1
    assert "1" in result["chunks"][0]["content"]
    assert "2" in result["chunks"][0]["content"]
    assert "3" not in result["chunks"][0]["content"]
    
    # 验证字幕范围
    assert result["chunks"][0]["subtitle_range"]["start"] == 1
    assert result["chunks"][0]["subtitle_range"]["end"] == 2


def test_split_srt_chunk_size_larger_than_total():
    """测试块大小大于总字幕数的情况"""
    result = split_srt(TEST_SRT, chunk_size=10)
    
    assert len(result["chunks"]) == 1  # 应该只有一个块
    assert result["total_subtitles"] == 5
    assert result["chunks"][0]["subtitle_range"]["start"] == 1
    assert result["chunks"][0]["subtitle_range"]["end"] == 5


def test_split_srt_complex_format():
    """测试复杂格式的 SRT 分割"""
    result = split_srt(COMPLEX_SRT, chunk_size=1)
    
    assert result["total_subtitles"] == 3
    assert len(result["chunks"]) == 3  # 每个字幕一个块
    
    # 验证多行文本和特殊字符是否保留
    assert "多行文本" in result["chunks"][0]["content"]
    assert "特殊字符" in result["chunks"][0]["content"]
    assert "对话格式" in result["chunks"][1]["content"]
    assert "<i>" in result["chunks"][2]["content"]
    assert "<b>" in result["chunks"][2]["content"]


def test_split_srt_irregular_format():
    """测试不规范格式的 SRT 分割，验证正则表达式解析功能"""
    result = split_srt(IRREGULAR_SRT, chunk_size=2)
    
    # 即使格式不规范，也应该能够正确解析
    assert result["total_subtitles"] == 3
    assert len(result["chunks"]) == 2
    
    # 验证内容是否正确分割
    first_chunk = result["chunks"][0]["content"]
    assert "1" in first_chunk
    assert "2" in first_chunk
    assert "3" not in first_chunk


def test_split_srt_empty():
    """测试空 SRT 内容的分割"""
    result = split_srt("", chunk_size=2)
    
    assert result["total_subtitles"] == 0
    assert len(result["chunks"]) == 0


def test_split_srt_no_subtitle_middle_split():
    """测试确保不会在字幕中间拆分"""
    # 创建一个包含多行文本的字幕
    multi_line_srt = """1
00:00:01,000 --> 00:00:04,000
这是第一行
这是第二行
这是第三行

2
00:00:05,000 --> 00:00:09,000
这是另一个字幕
"""
    
    result = split_srt(multi_line_srt, chunk_size=1)
    
    # 验证第一个字幕的所有行都在同一个块中
    first_chunk = result["chunks"][0]["content"]
    assert "这是第一行" in first_chunk
    assert "这是第二行" in first_chunk
    assert "这是第三行" in first_chunk
    
    # 验证没有将多行文本拆分到不同块
    assert "这是第一行" not in result["chunks"][1]["content"]


@pytest.mark.asyncio
async def test_srt_splitter_agent():
    """测试 SRT 分割智能体"""
    # 确保使用 Mistral 模型
    original_engine = settings.AGNO_SPLITTER_ENGINE
    settings.AGNO_SPLITTER_ENGINE = "mistral"
    
    # 创建智能体
    splitter = SRTSplitterAgent()
    
    # 分割 SRT 文件
    result = await splitter.split(TEST_SRT, chunk_size=2)
    
    assert "chunks" in result
    assert "total_subtitles" in result
    assert result["total_subtitles"] == 5
    assert len(result["chunks"]) == 3
    
    # 恢复原始设置
    settings.AGNO_SPLITTER_ENGINE = original_engine
