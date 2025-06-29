"""
执行工具模块

提供工作流执行相关的工具函数
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

from app.assistants.requirements.flow import RequirementsFlow
from app.core.reflection_engine import ReflectionEngine
from app.core.think_tool import ThinkTool
from app.logger import get_logger
from app.schema import RequirementAnalysisRequest, RequirementAnalysisResponse

logger = get_logger(__name__)


async def execute_flow_with_think_act_reflect(
    requirement_text: str, session_id: Optional[str] = None, **kwargs
) -> Dict[str, Any]:
    """
    使用思考-行动-反思模式执行需求分析工作流

    Args:
        requirement_text: 需求文本
        session_id: 会话ID
        **kwargs: 其他参数

    Returns:
        Dict[str, Any]: 分析结果
    """
    try:
        # 创建请求
        request = RequirementAnalysisRequest(
            requirement_text=requirement_text,
            session_id=session_id or f"session_{int(time.time())}",
            **kwargs
        )

        # 记录开始
        logger.info(f"开始执行需求分析工作流: {request.session_id}")

        # 创建工具
        think_tool = ThinkTool()
        reflection_engine = ReflectionEngine()

        # 思考阶段 - 分析需求
        logger.info("思考阶段: 分析需求")
        thinking_result = await think_tool.structured_thinking(
            requirement_text, 
            context={"session_id": request.session_id}
        )
        logger.info(f"思考完成，置信度: {thinking_result.confidence:.2f}")

        # 行动阶段 - 执行分析
        logger.info("行动阶段: 执行分析")
        flow = RequirementsFlow(session_id=request.session_id)
        flow_result = await flow.run(
            requirement_text=requirement_text,
            thinking_result=thinking_result,
            **kwargs
        )
        logger.info("分析执行完成")

        # 反思阶段 - 评估结果
        logger.info("反思阶段: 评估结果")
        reflection_result = await reflection_engine.comprehensive_reflection(
            original_input=requirement_text,
            generated_output=flow_result.get("analysis_results", {}).get("summary", ""),
            task_description="需求分析",
            evaluation_criteria=["完整性", "准确性", "清晰度", "可行性", "一致性"]
        )
        logger.info(f"反思完成，质量评分: {reflection_result.get('quality_score', 0):.2f}")

        # 创建响应
        response = RequirementAnalysisResponse(
            session_id=request.session_id,
            status="success",
            analysis_results=flow_result.get("analysis_results", {}),
            recommendations=reflection_result.get("improvement_suggestions", []),
            clarification_questions=flow_result.get("clarification_questions", []),
            next_steps=thinking_result.next_actions,
            metadata={
                "thinking_summary": thinking_result.summary,
                "reflection_insights": reflection_result.get("insights", []),
                "quality_score": reflection_result.get("quality_score", 0),
            }
        )

        return response.dict()

    except Exception as e:
        logger.error(f"执行需求分析工作流失败: {e}")
        if session_id:
            return RequirementAnalysisResponse(
                session_id=session_id,
                status="error",
                error=str(e),
            ).dict()
        else:
            return RequirementAnalysisResponse(
                session_id=f"error_{int(time.time())}",
                status="error",
                error=str(e),
            ).dict()
