"""
SRT 重组智能体

负责将翻译后的 SRT 块重新组合成完整的 SRT 文件，确保字幕 ID 连续。
"""

import re
import os
import aiofiles
from typing import Dict, Any, List, Optional

from agno.agent import Agent
from agno.tools import tool

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("app.agents.srt_reassembler")


@tool(
    name="reassemble_srt",
    description="将翻译后的 SRT 块重新组合成完整的 SRT 文件",
    show_result=True
)
def reassemble_srt(
    chunks: List[Dict[str, Any]],
    normalize_ids: bool = True
) -> Dict[str, Any]:
    """
    将翻译后的 SRT 块重新组合成完整的 SRT 文件。
    
    Args:
        chunks: 翻译后的 SRT 块列表，每个块包含 id 和 translated_content
        normalize_ids: 是否规范化字幕 ID（使其连续），默认为 True
        
    Returns:
        Dict[str, Any]: 包含重组结果的字典
            - content (str): 重组后的 SRT 内容
            - subtitle_count (int): 字幕数量
    """
    logger.info(f"开始重组 SRT 文件，块数量: {len(chunks)}")
    
    # 按块 ID 排序
    sorted_chunks = sorted(chunks, key=lambda x: x.get("id", 0))
    
    # 解析每个块的内容
    all_subtitles = []
    
    for chunk in sorted_chunks:
        translated_content = chunk.get("translated_content", "")
        
        # 解析字幕块
        subtitle_blocks = []
        current_block = []
        
        lines = translated_content.splitlines()
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
                if current_block:
                    subtitle_blocks.append(current_block)
                
                # 开始新的字幕块
                current_block = [line]
                i += 1
            except ValueError:
                # 不是字幕 ID，继续添加到当前块
                current_block.append(line)
                i += 1
        
        # 添加最后一个字幕块
        if current_block:
            subtitle_blocks.append(current_block)
        
        all_subtitles.extend(subtitle_blocks)
    
    # 规范化字幕 ID
    if normalize_ids:
        for i, subtitle in enumerate(all_subtitles):
            if subtitle:  # 确保字幕块不为空
                subtitle[0] = str(i + 1)
    
    # 组合成完整的 SRT 内容
    content = ""
    for subtitle in all_subtitles:
        if subtitle:  # 确保字幕块不为空
            content += "\n".join(subtitle) + "\n\n"
    
    result = {
        "content": content.strip(),
        "subtitle_count": len(all_subtitles)
    }
    
    logger.info(f"SRT 重组完成，字幕数量: {result['subtitle_count']}")
    
    return result


@tool(
    name="save_srt_file",
    description="将 SRT 内容保存到文件",
    show_result=True
)
async def save_srt_file(content: str, task_id: str, output_dir: str = "data/results") -> Dict[str, Any]:
    """
    将 SRT 内容保存到文件。
    
    Args:
        content: SRT 内容
        task_id: 任务 ID
        output_dir: 输出目录，默认为 "data/results"
        
    Returns:
        Dict[str, Any]: 包含保存结果的字典
            - file_path (str): 文件路径
            - file_size (int): 文件大小
    """
    logger.info(f"开始保存 SRT 文件，任务 ID: {task_id}")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件路径
    file_path = os.path.join(output_dir, f"{task_id}.srt")
    
    # 创建临时文件
    tmp_path = f"{file_path}.tmp"
    
    try:
        # 写入临时文件
        async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        # 原子重命名
        os.rename(tmp_path, file_path)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        result = {
            "file_path": file_path,
            "file_size": file_size
        }
        
        logger.info(f"SRT 文件保存成功: {file_path}，大小: {file_size} 字节")
        
        return result
    except Exception as e:
        logger.error(f"保存 SRT 文件失败: {str(e)}")
        
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        
        raise


class SRTReassemblerAgent:
    """SRT 重组智能体，负责将翻译后的 SRT 块重新组合成完整的 SRT 文件"""
    
    def __init__(self):
        """初始化 SRT 重组智能体"""
        # 使用配置的模型
        engine = settings.AGNO_REASSEMBLER_ENGINE
        logger.info(f"初始化 SRT 重组智能体，使用模型: {engine}")
        
        self.agent = Agent(
            tools=[reassemble_srt, save_srt_file],
            instructions=[
                "你是一个专业的 SRT 字幕重组助手",
                "你的任务是将翻译后的 SRT 块重新组合成完整的 SRT 文件，确保字幕 ID 连续",
                "只在需要时调用工具，不要主动调用"
            ],
            markdown=True,
            model=engine
        )
    
    async def reassemble(
        self,
        chunks: List[Dict[str, Any]],
        normalize_ids: bool = True
    ) -> Dict[str, Any]:
        """
        重组 SRT 内容
        
        Args:
            chunks: 翻译后的 SRT 块列表
            normalize_ids: 是否规范化字幕 ID
            
        Returns:
            Dict[str, Any]: 重组结果
        """
        try:
            # 直接调用工具函数，而不是通过 agent 处理
            result = reassemble_srt(chunks, normalize_ids)
            return result
        except Exception as e:
            logger.error(f"SRT 重组过程中发生错误: {str(e)}")
            return {
                "content": "",
                "subtitle_count": 0,
                "error": f"重组过程中发生错误: {str(e)}"
            }
    
    async def save_file(
        self,
        content: str,
        task_id: str,
        output_dir: str = "data/results"
    ) -> Dict[str, Any]:
        """
        保存 SRT 文件
        
        Args:
            content: SRT 内容
            task_id: 任务 ID
            output_dir: 输出目录
            
        Returns:
            Dict[str, Any]: 保存结果
        """
        try:
            # 直接调用工具函数，而不是通过 agent 处理
            result = await save_srt_file(content, task_id, output_dir)
            return result
        except Exception as e:
            logger.error(f"保存 SRT 文件过程中发生错误: {str(e)}")
            return {
                "file_path": "",
                "file_size": 0,
                "error": f"保存文件过程中发生错误: {str(e)}"
            }
