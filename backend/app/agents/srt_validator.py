"""
SRT 校验智能体

负责验证 SRT 文件格式是否正确，并提供错误定位。
"""

import re
from typing import Dict, Any, List, Optional

from agno.agent import Agent
from agno.tools import tool

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("app.agents.srt_validator")


@tool(
    name="validate_srt",
    description="验证 SRT 文件格式是否正确，并提供错误定位",
    show_result=True
)
def validate_srt(content: str) -> Dict[str, Any]:
    """
    验证 SRT 文件格式是否正确，并提供错误定位。
    
    Args:
        content: SRT 文件内容
        
    Returns:
        Dict[str, Any]: 包含验证结果的字典
            - valid (bool): 是否有效
            - errors (List[Dict]): 错误列表，每个错误包含行号和错误描述
    """
    logger.info("开始验证 SRT 文件")
    
    errors = []
    lines = content.splitlines()
    
    # 检查文件是否为空
    if not content.strip():
        return {
            "valid": False,
            "errors": [{"line": 0, "error": "SRT 文件为空"}]
        }
    
    # 按块处理 SRT 文件
    i = 0
    while i < len(lines):
        # 跳过空行
        if not lines[i].strip():
            i += 1
            continue
        
        # 检查序号
        try:
            subtitle_number = int(lines[i].strip())
            i += 1
        except ValueError:
            errors.append({
                "line": i + 1,
                "error": f"无效的字幕序号: '{lines[i]}'"
            })
            # 尝试跳到下一个块
            while i < len(lines) and lines[i].strip():
                i += 1
            continue
        
        # 检查时间轴格式
        if i >= len(lines):
            errors.append({
                "line": i,
                "error": "缺少时间轴"
            })
            break
        
        time_line = lines[i]
        time_pattern = r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})'
        if not re.match(time_pattern, time_line):
            errors.append({
                "line": i + 1,
                "error": f"无效的时间轴格式: '{time_line}'"
            })
        i += 1
        
        # 检查字幕文本
        if i >= len(lines):
            errors.append({
                "line": i,
                "error": "缺少字幕文本"
            })
            break
        
        # 读取字幕文本直到遇到空行或文件结束
        has_text = False
        while i < len(lines) and lines[i].strip():
            has_text = True
            i += 1
        
        if not has_text:
            errors.append({
                "line": i,
                "error": "字幕文本为空"
            })
        
        # 跳过空行
        while i < len(lines) and not lines[i].strip():
            i += 1
    
    result = {
        "valid": len(errors) == 0,
        "errors": errors
    }
    
    logger.info(f"SRT 验证完成，结果: {result['valid']}")
    if not result['valid']:
        logger.warning(f"SRT 验证失败，错误: {errors}")
    
    return result


class SRTValidatorAgent:
    """SRT 验证智能体，负责验证 SRT 文件格式"""
    
    def __init__(self):
        """初始化 SRT 验证智能体"""
        # 使用配置的模型
        engine = settings.AGNO_VALIDATOR_ENGINE
        logger.info(f"初始化 SRT 验证智能体，使用模型: {engine}")
        
        self.agent = Agent(
            tools=[validate_srt],
            instructions=[
                "你是一个专业的 SRT 字幕文件验证助手",
                "你的任务是验证 SRT 文件格式是否正确，并提供详细的错误信息",
                "只在需要时调用工具，不要主动调用"
            ],
            markdown=True,
            model=engine
        )
    
    async def validate(self, content: str) -> Dict[str, Any]:
        """
        验证 SRT 文件内容
        
        Args:
            content: SRT 文件内容
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 直接调用工具函数，而不是通过 agent 处理
            result = validate_srt(content)
            return result
        except Exception as e:
            logger.error(f"SRT 验证过程中发生错误: {str(e)}")
            return {
                "valid": False,
                "errors": [{"line": 0, "error": f"验证过程中发生错误: {str(e)}"}]
            }
