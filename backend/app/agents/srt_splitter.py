"""
SRT 分块智能体

负责将 SRT 文件分成更小的块进行处理，保留上下文关系。
"""

import re
from typing import Dict, Any, List, Optional

from agno.agent import Agent
from agno.tools import tool

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("app.agents.srt_splitter")


@tool(
    name="split_srt",
    description="将 SRT 文件分成更小的块进行处理，保留上下文关系",
    show_result=True
)
def split_srt(content: str, chunk_size: int = 100) -> Dict[str, Any]:
    """
    将 SRT 文件分成更小的块进行处理，保留上下文关系。
    
    Args:
        content: SRT 文件内容
        chunk_size: 每个块的最大字幕数量，默认为 100
        
    Returns:
        Dict[str, Any]: 包含分块结果的字典
            - chunks (List[Dict]): 分块列表，每个块包含 id、内容和字幕范围
            - total_subtitles (int): 总字幕数量
    """
    logger.info(f"开始分块 SRT 文件，块大小: {chunk_size}")
    
    # 使用正则表达式匹配 SRT 格式的字幕块
    # SRT 格式: 序号 + 时间码 + 字幕内容 + 空行
    pattern = r'(\d+)\s*\n([\d:,\s->]+)\s*\n([\s\S]*?)(?=\n\s*\n\s*\d+\s*\n|$)'
    matches = re.finditer(pattern, content)
    
    # 解析 SRT 文件，确保每个字幕块完整
    subtitle_blocks = []
    
    for match in matches:
        subtitle_id = int(match.group(1))
        timing = match.group(2)
        subtitle_text = match.group(3).strip()
        
        subtitle_blocks.append({
            "id": subtitle_id,
            "content": f"{subtitle_id}\n{timing}\n{subtitle_text}"
        })
    
    # 如果没有找到任何字幕块，尝试使用传统的解析方法
    if not subtitle_blocks:
        logger.warning("正则表达式解析失败，尝试使用传统解析方法")
        subtitle_blocks = []
        current_block = []
        current_subtitle_id = None
        
        lines = content.splitlines()
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行
            if not line:
                i += 1
                continue
            
            # 检查是否是新的字幕块
            try:
                subtitle_id = int(line)
                
                # 如果已经有一个字幕块在处理，保存它
                if current_block and current_subtitle_id is not None:
                    subtitle_blocks.append({
                        "id": current_subtitle_id,
                        "content": "\n".join(current_block)
                    })
                
                # 开始新的字幕块
                current_subtitle_id = subtitle_id
                current_block = [line]
                i += 1
            except ValueError:
                # 不是字幕 ID，继续添加到当前块
                if current_block:
                    current_block.append(line)
                i += 1
        
        # 添加最后一个字幕块
        if current_block and current_subtitle_id is not None:
            subtitle_blocks.append({
                "id": current_subtitle_id,
                "content": "\n".join(current_block)
            })
    
    # 注意：在使用传统解析方法时，最后一个字幕块已经在循环内添加了
    
    # 将字幕块分成更大的处理块
    chunks = []
    total_blocks = len(subtitle_blocks)
    
    for i in range(0, total_blocks, chunk_size):
        end_idx = min(i + chunk_size, total_blocks)
        chunk_blocks = subtitle_blocks[i:end_idx]
        
        # 创建块
        chunk = {
            "id": len(chunks) + 1,
            "content": "\n\n".join([block["content"] for block in chunk_blocks]),
            "subtitle_range": {
                "start": chunk_blocks[0]["id"],
                "end": chunk_blocks[-1]["id"]
            }
        }
        
        chunks.append(chunk)
    
    result = {
        "chunks": chunks,
        "total_subtitles": total_blocks
    }
    
    logger.info(f"SRT 分块完成，共 {len(chunks)} 个块，{total_blocks} 个字幕")
    
    return result


class SRTSplitterAgent:
    """SRT 分块智能体，负责将 SRT 文件分成更小的块进行处理"""
    
    def __init__(self):
        """初始化 SRT 分块智能体"""
        # 使用配置的模型
        engine = settings.AGNO_SPLITTER_ENGINE
        logger.info(f"初始化 SRT 分块智能体，使用模型: {engine}")
        
        self.agent = Agent(
            tools=[split_srt],
            instructions=[
                "你是一个专业的 SRT 字幕文件分块助手",
                "你的任务是将 SRT 文件分成更小的块进行处理，保留上下文关系",
                "只在需要时调用工具，不要主动调用"
            ],
            markdown=True,
            model=engine
        )
    
    async def split(self, content: str, chunk_size: int = 100) -> Dict[str, Any]:
        """
        将 SRT 文件分成更小的块进行处理
        
        Args:
            content: SRT 文件内容
            chunk_size: 每个块的最大字幕数量，默认为 100
            
        Returns:
            Dict[str, Any]: 分块结果
        """
        try:
            # 直接调用工具函数，而不是通过 agent 处理
            result = split_srt(content, chunk_size)
            return result
        except Exception as e:
            logger.error(f"SRT 分块过程中发生错误: {str(e)}")
            return {
                "chunks": [],
                "total_subtitles": 0,
                "error": f"分块过程中发生错误: {str(e)}"
            }
