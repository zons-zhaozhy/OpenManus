"""
需求澄清路由模块
"""

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from app.logger import logger
from app.schema import ClarificationRequest, ClarificationResponse

from ..utils.clarification import (
    process_clarification_answer,
    process_clarification_question,
)

clarification_router = APIRouter(prefix="/clarification", tags=["需求澄清"])


@clarification_router.post("/question", response_model=ClarificationResponse)
async def generate_clarification_question(
    request: ClarificationRequest,
) -> Dict[str, Any]:
    """
    生成澄清问题

    Args:
        request: 澄清请求，包含：
            - requirement: 需求文本
            - context: 可选的上下文信息，包含：
                - mode: 分析模式 ("quick", "standard", "deep")，默认为"standard"

    Returns:
        Dict[str, Any]: 澄清问题
    """
    try:
        # 输入验证
        if not request.requirement or request.requirement.strip() == "":
            raise ValueError("需求内容不能为空")

        # 添加超时处理
        result = await asyncio.wait_for(
            process_clarification_question(request.requirement, request.context or {}),
            timeout=35,  # 比智能体超时时间稍长
        )
        return result
    except ValueError as e:
        logger.error(f"输入参数无效: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except asyncio.TimeoutError:
        logger.error("澄清问题生成超时")
        mode = (
            request.context.get("mode", "standard") if request.context else "standard"
        )
        if mode != "quick":
            error_msg = "请求超时 - 建议使用quick模式以获得更快的响应"
        else:
            error_msg = "请求超时 - 请稍后重试或简化需求内容"
        raise HTTPException(status_code=408, detail=error_msg)
    except Exception as e:
        logger.error(f"生成澄清问题失败: {e}")
        raise HTTPException(
            status_code=500, detail="需求澄清过程中发生错误，请检查输入并重试"
        )


@clarification_router.post("/answer", response_model=ClarificationResponse)
async def process_answer(
    request: ClarificationRequest,
) -> Dict[str, Any]:
    """
    处理澄清答案

    Args:
        request: 澄清请求，包含：
            - session_id: 会话ID
            - requirement: 需求文本
            - context: 可选的上下文信息，包含：
                - mode: 分析模式 ("quick", "standard", "deep")，默认为"standard"
                - question: 问题
                - answer: 用户答案

    Returns:
        Dict[str, Any]: 处理结果
    """
    try:
        # 输入验证
        if not request.requirement or request.requirement.strip() == "":
            raise ValueError("需求内容不能为空")

        if (
            not request.context
            or "question" not in request.context
            or "answer" not in request.context
        ):
            raise ValueError("缺少必要的问题和答案信息")

        if not request.context["question"] or not request.context["answer"]:
            raise ValueError("问题和答案不能为空")

        result = await process_clarification_answer(
            request.context["question"], request.context["answer"], request.context
        )
        return result
    except ValueError as e:
        logger.error(f"输入参数无效: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"处理澄清答案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
