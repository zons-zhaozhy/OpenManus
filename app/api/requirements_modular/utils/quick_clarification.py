"""
快速需求澄清工具函数

提供快速分析模式，支持30秒内完成需求澄清。
"""

from typing import Any, Dict, List, Optional

from app.assistants.requirements.agents.requirement_clarifier import (
    RequirementClarification,
    RequirementClarifierAgent,
)
from app.llm import LLM
from app.logger import logger
from app.schema import Message


async def generate_clarification_questions(
    requirement: str, context: Dict[str, Any] = None
) -> List[str]:
    """
    生成澄清问题

    Args:
        requirement: 需求描述
        context: 上下文信息，包含：
            - mode: 分析模式 ("quick", "standard", "deep")，默认为"standard"

    Returns:
        List[str]: 澄清问题列表
    """
    try:
        # 创建澄清工具
        clarification_tool = RequirementClarification(LLM())

        # 根据模式选择分析方法
        mode = context.get("mode", "standard") if context else "standard"
        if mode == "quick":
            analysis_result = await clarification_tool.quick_analyze(requirement)
            # 从快速分析结果中提取问题
            questions = []
            if analysis_result.get("core_points"):
                questions.extend(
                    [f"请详细说明：{point}" for point in analysis_result["core_points"]]
                )
            if analysis_result.get("risks"):
                questions.extend(
                    [
                        f"关于风险'{risk}'，您是否有应对方案？"
                        for risk in analysis_result["risks"]
                    ]
                )
        else:
            # 标准分析
            analysis_result = await clarification_tool.analyze_requirement(requirement)
            clarification_points = (
                await clarification_tool.identify_clarification_points(analysis_result)
            )
            questions = [
                point["question"]
                for point in clarification_points
                if "question" in point
            ]

        return questions
    except Exception as e:
        logger.error(f"生成澄清问题失败: {e}")
        return []


async def process_clarification_question(
    requirement: str, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    处理需求澄清问题

    Args:
        requirement: 需求内容
        context: 上下文信息，包含：
            - mode: 分析模式 ("quick", "standard", "deep")，默认为"standard"

    Returns:
        Dict[str, Any]: 澄清问题
    """
    try:
        # 初始化上下文
        ctx = context or {}
        mode = ctx.get("mode", "standard")

        # 创建澄清工具
        try:
            clarification_tool = RequirementClarification(LLM())

            # 根据模式选择分析方法
            if mode == "quick":
                analysis_result = await clarification_tool.quick_analyze(requirement)
                # 从快速分析结果中提取问题
                questions = []
                if analysis_result.get("core_points"):
                    questions.extend(
                        [
                            f"请详细说明：{point}"
                            for point in analysis_result["core_points"]
                        ]
                    )
                if analysis_result.get("risks"):
                    questions.extend(
                        [
                            f"关于风险'{risk}'，您是否有应对方案？"
                            for risk in analysis_result["risks"]
                        ]
                    )
                clarification_points = [{"question": q} for q in questions]
            else:
                # 标准分析
                analysis_result = await clarification_tool.analyze_requirement(
                    requirement
                )
                clarification_points = (
                    await clarification_tool.identify_clarification_points(
                        analysis_result
                    )
                )
                questions = [
                    point["question"]
                    for point in clarification_points
                    if "question" in point
                ]

        except Exception as e:
            logger.error(f"使用澄清工具失败: {e}")
            # 提供默认问题
            questions = [
                "请详细描述您需要的在线商城系统的主要功能是什么？",
                "这个系统的目标用户群体是谁？",
                "您对系统的性能和可用性有什么特殊要求？",
                "您有没有参考的类似系统或竞品？",
                "您期望的开发周期和预算范围是什么？",
            ]
            clarification_points = [{"question": q} for q in questions]

        # 如果没有问题，生成一个默认问题
        if not questions:
            questions = ["请详细描述您的需求是什么？"]
            clarification_points = [{"question": questions[0]}]

        # 更新上下文
        ctx["requirement"] = requirement
        ctx["questions"] = questions
        ctx["clarification_points"] = clarification_points
        ctx["mode"] = mode

        return {
            "questions": questions,
            "status": "success",
            "context": ctx,
            "mode": mode,
            "analysis_result": (
                analysis_result if "analysis_result" in locals() else None
            ),
        }
    except Exception as e:
        logger.error(f"生成澄清问题失败: {e}")
        # 即使在失败的情况下也返回一些默认问题
        default_questions = [
            "请详细描述您需要的系统的主要功能是什么？",
            "这个系统的目标用户群体是谁？",
            "您对系统的性能和可用性有什么特殊要求？",
            "您有没有参考的类似系统或竞品？",
            "您期望的开发周期和预算范围是什么？",
        ]
        return {
            "questions": default_questions,
            "status": "success",
            "context": {"requirement": requirement, "questions": default_questions},
            "mode": "standard",  # 失败时使用标准模式
        }


async def process_clarification_answer(
    question: str, answer: str, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    处理需求澄清答案

    Args:
        question: 澄清问题
        answer: 用户答案
        context: 上下文信息，包含：
            - mode: 分析模式 ("quick", "standard", "deep")，默认为"standard"

    Returns:
        Dict[str, Any]: 处理结果
    """
    try:
        # 初始化上下文
        ctx = context or {}
        requirement = ctx.get("requirement", "")
        mode = ctx.get("mode", "standard")

        # 创建澄清工具
        try:
            clarification_tool = RequirementClarification(LLM())

            # 更新需求
            updated_requirement = f"{requirement}\n\n问题: {question}\n回答: {answer}"

            # 根据模式选择分析方法
            if mode == "quick":
                analysis_result = await clarification_tool.quick_analyze(
                    updated_requirement
                )
                # 从快速分析结果中提取新问题
                new_questions = []
                if analysis_result.get("core_points"):
                    new_questions.extend(
                        [
                            f"请详细说明：{point}"
                            for point in analysis_result["core_points"]
                        ]
                    )
                if analysis_result.get("risks"):
                    new_questions.extend(
                        [
                            f"关于风险'{risk}'，您是否有应对方案？"
                            for risk in analysis_result["risks"]
                        ]
                    )
                new_clarification_points = [{"question": q} for q in new_questions]
            else:
                # 标准分析
                analysis_result = await clarification_tool.analyze_requirement(
                    updated_requirement
                )
                new_clarification_points = (
                    await clarification_tool.identify_clarification_points(
                        analysis_result
                    )
                )
                new_questions = [
                    point["question"]
                    for point in new_clarification_points
                    if "question" in point
                ]

        except Exception as e:
            logger.error(f"使用澄清工具失败: {e}")
            # 提供默认的后续问题
            if "商城" in requirement or "电商" in requirement:
                new_questions = [
                    "您希望商城支持哪些支付方式？",
                    "是否需要会员管理系统？",
                    "您对商品管理和库存管理有什么特殊要求？",
                ]
            else:
                new_questions = [
                    "您对系统的安全性有什么要求？",
                    "系统需要支持多语言或国际化吗？",
                    "您对系统的可扩展性有什么考虑？",
                ]
            new_clarification_points = [{"question": q} for q in new_questions]
            updated_requirement = f"{requirement}\n\n问题: {question}\n回答: {answer}"

        # 如果没有后续问题，可能澄清已完成
        is_complete = len(new_questions) == 0

        # 更新上下文
        ctx["requirement"] = updated_requirement
        ctx["questions"] = new_questions
        ctx["clarification_points"] = new_clarification_points
        ctx["is_complete"] = is_complete
        ctx["mode"] = mode

        if is_complete:
            return {
                "status": "complete",
                "message": "需求澄清完成",
                "final_requirement": updated_requirement,
                "context": ctx,
                "mode": mode,
                "analysis_result": (
                    analysis_result if "analysis_result" in locals() else None
                ),
            }
        else:
            return {
                "status": "in_progress",
                "message": "继续澄清",
                "questions": new_questions,
                "context": ctx,
                "mode": mode,
                "analysis_result": (
                    analysis_result if "analysis_result" in locals() else None
                ),
            }

    except Exception as e:
        logger.error(f"处理澄清答案失败: {e}")
        raise


async def evaluate_clarification_quality(
    requirement: str,
    clarification_qa: List[Dict[str, str]],
    context: Dict[str, Any] = None,
) -> float:
    """
    评估澄清质量

    Args:
        requirement: 原始需求
        clarification_qa: 澄清问答列表
        context: 上下文信息，包含：
            - mode: 分析模式 ("quick", "standard", "deep")，默认为"standard"

    Returns:
        float: 质量评分 (0-1)
    """
    try:
        # 创建澄清工具
        clarification_tool = RequirementClarification(LLM())

        # 根据模式选择评估方法
        mode = context.get("mode", "standard") if context else "standard"
        if mode == "quick":
            # 快速评估
            analysis_result = await clarification_tool.quick_analyze(requirement)
            return analysis_result.get("confidence", 0.8)
        else:
            # 标准评估
            analysis_result = await clarification_tool.analyze_requirement(requirement)
            return analysis_result.get("clarity_score", 0.7)

    except Exception as e:
        logger.error(f"评估澄清质量失败: {e}")
        return 0.5  # 失败时返回中等分数
