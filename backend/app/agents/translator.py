"""
翻译执行智能体

负责将分块后的 SRT 内容翻译成目标语言，支持多种翻译引擎和术语表替换。
"""

import re
import json
from typing import Dict, Any, List, Optional

from agno.agent import Agent
from agno.tools import tool

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("app.agents.translator")


@tool(
    name="translate_chunk",
    description="翻译 SRT 字幕块",
    show_result=True
)
def translate_chunk(
    content: str,
    source_lang: str,
    target_lang: str,
    glossary: Optional[Dict[str, str]] = None,
    engine: str = "deepseek"
) -> Dict[str, Any]:
    """
    翻译 SRT 字幕块。
    
    Args:
        content: SRT 字幕块内容
        source_lang: 源语言代码
        target_lang: 目标语言代码
        glossary: 术语表，键为源语言术语，值为目标语言术语
        engine: 翻译引擎，可选值为 "deepseek"（默认）或 "mistral"
        
    Returns:
        Dict[str, Any]: 包含翻译结果的字典
            - translated_content (str): 翻译后的内容
            - engine (str): 使用的翻译引擎
            - glossary_matches (List[Dict]): 术语表匹配列表
    """
    logger.info(f"开始翻译 SRT 块，源语言: {source_lang}，目标语言: {target_lang}，引擎: {engine}")
    
    # 解析 SRT 块
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
                    "content": "\n".join(current_block),
                    "lines": current_block.copy()
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
            "content": "\n".join(current_block),
            "lines": current_block.copy()
        })
    
    # 翻译每个字幕块
    translated_blocks = []
    glossary_matches = []
    
    for block in subtitle_blocks:
        # 提取时间轴和文本
        if len(block["lines"]) < 3:
            logger.warning(f"字幕块格式不正确，跳过翻译: {block}")
            translated_blocks.append(block)
            continue
        
        subtitle_id = block["lines"][0]
        time_line = block["lines"][1]
        text_lines = block["lines"][2:]
        text = "\n".join(text_lines)
        
        # 应用术语表替换
        if glossary:
            for term, translation in glossary.items():
                if term.lower() in text.lower():
                    glossary_matches.append({
                        "subtitle_id": subtitle_id,
                        "term": term,
                        "translation": translation
                    })
        
        # 根据引擎选择翻译方法
        translated_text = ""
        if engine == "deepseek" and settings.DEEPSEEK_API_KEY:
            translated_text = _translate_with_deepseek(text, source_lang, target_lang, glossary)
        elif engine == "mistral":
            translated_text = _translate_with_mistral(text, source_lang, target_lang, glossary)
        else:
            # 默认使用 DeepSeek
            logger.warning(f"未知引擎 {engine} 或配置缺失，使用 DeepSeek 作为后备")
            translated_text = _translate_with_deepseek(text, source_lang, target_lang, glossary)
        
        # 构建翻译后的字幕块
        translated_block = {
            "id": block["id"],
            "content": f"{subtitle_id}\n{time_line}\n{translated_text}",
            "lines": [subtitle_id, time_line] + translated_text.splitlines()
        }
        
        translated_blocks.append(translated_block)
    
    # 组合翻译后的内容
    translated_content = "\n\n".join([block["content"] for block in translated_blocks])
    
    result = {
        "translated_content": translated_content,
        "engine": engine,
        "glossary_matches": glossary_matches
    }
    
    logger.info(f"SRT 块翻译完成，引擎: {engine}，匹配术语: {len(glossary_matches)}")
    
    return result


def _translate_with_deepseek(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary: Optional[Dict[str, str]] = None
) -> str:
    """
    使用 DeepSeek API 翻译文本
    
    Args:
        text: 要翻译的文本
        source_lang: 源语言代码
        target_lang: 目标语言代码
        glossary: 术语表
        
    Returns:
        str: 翻译后的文本
    """
    logger.info("使用 DeepSeek API 翻译")
    
    # 在实际实现中，这里应该调用 DeepSeek API
    # 为了示例，我们使用一个简单的模拟实现
    
    # 应用术语表替换
    translated_text = f"[{source_lang} -> {target_lang}] {text}"
    
    if glossary:
        for term, translation in glossary.items():
            if term.lower() in text.lower():
                # 使用正则表达式进行大小写敏感的替换
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                translated_text = pattern.sub(translation, translated_text)
    
    return translated_text


def _translate_with_mistral(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary: Optional[Dict[str, str]] = None
) -> str:
    """
    使用 Mistral API 翻译文本
    
    Args:
        text: 要翻译的文本
        source_lang: 源语言代码
        target_lang: 目标语言代码
        glossary: 术语表
        
    Returns:
        str: 翻译后的文本
    """
    logger.info("使用 Mistral API 翻译")
    
    # 在实际实现中，这里应该调用 Mistral API
    # 参考 Agno 文档：https://docs.agno.com/models/mistral
    # 为了示例，我们使用一个简单的模拟实现
    
    # 应用术语表替换
    translated_text = f"[Mistral: {source_lang} -> {target_lang}] {text}"
    
    if glossary:
        for term, translation in glossary.items():
            if term.lower() in text.lower():
                # 使用正则表达式进行大小写敏感的替换
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                translated_text = pattern.sub(translation, translated_text)
    
    return translated_text


class TranslatorAgent:
    """翻译执行智能体，负责将 SRT 内容翻译成目标语言"""
    
    def __init__(self):
        """初始化翻译执行智能体"""
        # 使用配置的模型
        engine = settings.AGNO_TRANSLATOR_ENGINE
        logger.info(f"初始化翻译执行智能体，使用模型: {engine}")
        
        self.agent = Agent(
            tools=[translate_chunk],
            instructions=[
                "你是一个专业的 SRT 字幕翻译助手",
                "你的任务是将 SRT 字幕内容翻译成目标语言，同时保持原始格式",
                "只在需要时调用工具，不要主动调用"
            ],
            markdown=True,
            model=engine
        )
    
    async def translate(
        self,
        content: str,
        source_lang: str,
        target_lang: str,
        glossary: Optional[Dict[str, str]] = None,
        engine: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        翻译 SRT 内容
        
        Args:
            content: SRT 内容
            source_lang: 源语言代码
            target_lang: 目标语言代码
            glossary: 术语表
            engine: 翻译引擎（可选，如果不指定则使用默认引擎）
            
        Returns:
            Dict[str, Any]: 翻译结果
        """
        try:
            # 如果未指定引擎，使用默认引擎
            if engine is None:
                engine = settings.AGNO_DEFAULT_ENGINE
                logger.info(f"使用默认翻译引擎: {engine}")
            
            # 直接调用工具函数，而不是通过 agent 处理
            result = translate_chunk(content, source_lang, target_lang, glossary, engine)
            return result
        except Exception as e:
            logger.error(f"SRT 翻译过程中发生错误: {str(e)}")
            return {
                "translated_content": "",
                "engine": engine,
                "glossary_matches": [],
                "error": f"翻译过程中发生错误: {str(e)}"
            }
