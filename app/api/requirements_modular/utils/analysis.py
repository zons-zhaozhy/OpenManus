"""
分析工具模块

提供需求分析相关的工具函数
"""

import asyncio
from typing import AsyncGenerator, Dict

from fastapi.responses import StreamingResponse

from app.assistants.requirements.flow import RequirementsFlow
from app.core.adaptive_learning_system import adaptive_learning_system
from app.logger import logger

from ..exceptions import AnalysisError


async def create_analysis_stream(content: str) -> StreamingResponse:
    """创建分析流"""
    try:
        return StreamingResponse(
            _generate_analysis_stream(content),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"创建分析流失败: {str(e)}")
        raise AnalysisError(f"创建分析流失败: {str(e)}")


async def _generate_analysis_stream(content: str) -> AsyncGenerator[str, None]:
    """生成分析流"""
    try:
        flow = RequirementsFlow()
        async for event in flow.execute_stream(content):
            # 转换事件为SSE格式
            yield f"data: {event}\n\n"
    except Exception as e:
        logger.error(f"生成分析流失败: {str(e)}")
        yield f"event: error\ndata: {str(e)}\n\n"


async def analyze_with_timeout(content: str, timeout: float) -> Dict:
    """带超时的分析"""
    try:
        flow = RequirementsFlow()
        result = await asyncio.wait_for(flow.execute(content), timeout=timeout)

        # 更新学习系统
        adaptive_learning_system.add_analysis_result(
            content=content,
            result=result,
            processing_time=result.get("processing_time", 0.0),
        )

        return result
    except asyncio.TimeoutError:
        logger.error(f"分析超时 (timeout={timeout}s)")
        raise AnalysisError(f"分析超时 (timeout={timeout}s)")
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise AnalysisError(f"分析失败: {str(e)}")


async def analyze_with_retry(
    content: str, max_retries: int = 3, base_timeout: float = 30.0
) -> Dict:
    """带重试的分析"""
    last_error = None
    timeout = base_timeout

    for attempt in range(max_retries):
        try:
            return await analyze_with_timeout(content, timeout)
        except AnalysisError as e:
            last_error = e
            timeout *= 1.5  # 增加超时时间
            logger.warning(f"分析失败，尝试重试 ({attempt + 1}/{max_retries})")
            await asyncio.sleep(1)  # 等待一秒再重试

    raise last_error or AnalysisError("分析失败，已达到最大重试次数")
