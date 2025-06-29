"""
需求分析模块工具函数

提供需求分析相关的工具函数
"""

import asyncio
import hashlib
import time
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

from app.assistants.requirements.flow import RequirementsFlow
from app.core.adaptive_learning_system import AnalysisCase, adaptive_learning_system
from app.core.performance_controller import get_performance_controller
from app.logger import logger

from .storage import session_storage

# 活跃会话存储
active_sessions: Dict = {}

__all__ = [
    "active_sessions",
    "execute_flow_with_think_act_reflect",
    "generate_clarification_questions",
    "process_clarification_answer",
    "create_analysis_stream",
    "generate_workflow_stream",
    "get_session_progress",
    "analyze_user_requirement",
]


async def execute_flow_with_think_act_reflect(content: str) -> Dict:
    """
    执行带有思-行-反思循环的流。
    此函数会初始化一个 RequirementsFlow 并执行它。
    """
    # 生成会话ID用于缓存和跟踪
    content_hash = hashlib.md5(content.encode()).hexdigest()
    cache_key = f"flow_result:{content_hash}"

    # 检查缓存
    if cache_key in session_storage._storage:
        logger.info(f"使用缓存结果: {cache_key}")
        return session_storage._storage[cache_key]

    # 创建流实例
    flow = RequirementsFlow(enable_parallel=True)

    # 设置进度回调
    async def progress_callback(step: int, total: int, stage: str):
        logger.info(f"执行进度: {step}/{total} - {stage}")

    try:
        # 执行需求分析流程，传入进度回调
        start_time = time.time()
        result = await flow.execute(
            user_input=content, progress_callback=progress_callback
        )
        processing_time = time.time() - start_time

        # 添加处理时间到结果
        result["processing_time"] = processing_time

        # 记录分析案例（简化）
        case = AnalysisCase(
            case_id=flow.session_id,  # 使用session_id作为case_id
            user_input=content,
            initial_analysis=result.get("final_result", {}),
            clarification_questions=result.get("clarification_questions", []),
            user_answers=[],  # 初始为空
            final_quality=result.get("quality_metrics", {}).get("overall_quality", 0.0),
            user_satisfaction=0.0,  # 初始为0
            completion_time=processing_time,
            success_indicators={
                "has_questions": bool(result.get("clarification_questions")),
                "pattern_recognized": False,  # TODO: Add actual pattern recognition
                "initial_confidence": result.get("quality_metrics", {}).get(
                    "overall_quality", 0
                ),
            },
            timestamp=datetime.now(),
        )

        # 保存案例
        adaptive_learning_system.record_analysis_case(case)

        # 缓存结果
        session_storage._storage[cache_key] = result

        return result
    except Exception as e:
        logger.error(f"执行Flow失败: {str(e)}")
        return {"error": f"执行失败: {str(e)}"}


async def generate_clarification_questions(content: str) -> List[str]:
    """生成澄清问题"""
    try:
        from app.core.interactive_clarification_handler import (
            InteractionSignal,
            InteractiveClarificationHandler,
        )

        # 创建交互式澄清处理器
        handler = InteractiveClarificationHandler()

        # 初始化会话并获取初始问题
        session = await handler.initialize_session(content)

        # 获取针对性问题
        result = await handler.process_interaction(
            signal=InteractionSignal.NEED_CLARIFICATION,
            payload={"original_text": content},
        )

        # 如果有问题，返回问题列表
        if "questions" in result and result["questions"]:
            return result["questions"]

        # 否则返回基础问题
        return [
            "您能详细描述一下系统的主要功能吗？",
            "您对系统的性能有什么具体要求？",
            "系统需要支持哪些用户角色？",
        ]
    except Exception as e:
        logger.error(f"生成澄清问题失败: {str(e)}")
        return []


async def process_clarification_answer(content: str, context: Dict) -> Dict:
    """处理澄清回答"""
    try:
        from app.core.interactive_clarification_handler import (
            InteractionSignal,
            InteractiveClarificationHandler,
        )

        # 创建交互式澄清处理器
        handler = InteractiveClarificationHandler()

        # 获取会话ID
        session_id = context.get("session_id")
        if not session_id:
            # 如果没有会话ID，创建新会话
            session = await handler.initialize_session(context.get("original_text", ""))
            session_id = session.session_id

        # 处理用户回答
        result = await handler.process_interaction(
            signal=InteractionSignal.PROVIDE_INFORMATION,
            payload={
                "session_id": session_id,
                "question": context.get("current_question", ""),
                "answer": content,
                "context": context,
            },
        )

        # 构建响应
        response = {
            "status": "clarifying",
            "session_id": session_id,
            "context": context,
        }

        # 添加后续问题
        if "questions" in result and result["questions"]:
            response["next_questions"] = result["questions"]
        else:
            response["next_questions"] = []

        # 检查是否完成澄清
        if "clarity_score" in result and result["clarity_score"] >= 0.8:
            response["status"] = "completed"

        return response
    except Exception as e:
        logger.error(f"处理澄清回答失败: {str(e)}")
        return {"error": f"处理失败: {str(e)}"}


async def generate_workflow_stream(session_id: str) -> AsyncGenerator[Dict, None]:
    """
    生成工作流事件流

    Args:
        session_id: 会话ID

    Yields:
        Dict: 工作流事件数据
    """
    try:
        session_data = session_storage.get_session(session_id)
        if not session_data:
            raise ValueError(f"无效的会话ID: {session_id}")

        # 生成工作流事件
        total_steps = 5
        for step in range(total_steps):
            # 模拟处理时间
            await asyncio.sleep(1)

            # 生成进度事件
            progress = (step + 1) / total_steps * 100
            yield {
                "event": "progress",
                "data": {
                    "percentage": progress,
                    "stage": "分析中" if progress < 100 else "完成",
                    "step": step + 1,
                    "total_steps": total_steps,
                },
            }

    except Exception as e:
        logger.error(f"生成工作流事件流失败: {str(e)}")
        yield {"error": f"生成失败: {str(e)}"}


def get_session_progress(session_id: str) -> Dict:
    """
    获取会话进度

    Args:
        session_id: 会话ID

    Returns:
        Dict: 进度信息
    """
    try:
        session_data = session_storage.get_session(session_id)
        if not session_data:
            raise ValueError(f"无效的会话ID: {session_id}")

        return session_storage.get_session_progress(session_id)

    except Exception as e:
        logger.error(f"获取会话进度失败: {str(e)}")
        return {"error": f"获取失败: {str(e)}"}


async def create_analysis_stream(
    content: str, project_context: str = None
) -> AsyncGenerator[Dict, None]:
    """
    创建分析流

    Args:
        content: 需求内容
        project_context: 项目上下文

    Yields:
        Dict: 分析事件数据
    """
    try:
        # 获取性能控制器
        performance_controller = get_performance_controller()

        # 设置超时
        timeout = performance_controller.get_dynamic_timeout(
            base_timeout=300.0, task_type="analysis_stream"
        )

        # 创建分析任务
        analysis_task = asyncio.create_task(
            execute_flow_with_think_act_reflect(content)
        )

        # 等待分析完成或超时
        try:
            result = await asyncio.wait_for(analysis_task, timeout)

            # 生成分析事件
            yield {"event": "analysis_complete", "data": result}

        except asyncio.TimeoutError:
            logger.warning(f"分析流生成超时 (timeout={timeout}s)")
            yield {"error": "分析超时"}

    except Exception as e:
        logger.error(f"创建分析流失败: {str(e)}")
        yield {"error": f"创建失败: {str(e)}"}


async def analyze_user_requirement(content: str) -> Dict:
    """
    分析用户需求

    Args:
        content: 需求内容

    Returns:
        Dict: 分析结果
    """
    try:
        # 获取性能控制器
        performance_controller = get_performance_controller()

        # 设置超时
        timeout = performance_controller.get_dynamic_timeout(
            base_timeout=300.0, task_type="requirement_analysis"
        )

        # 创建分析任务
        analysis_task = asyncio.create_task(
            execute_flow_with_think_act_reflect(content)
        )

        # 等待分析完成或超时
        try:
            result = await asyncio.wait_for(analysis_task, timeout)
            return result

        except asyncio.TimeoutError:
            logger.warning(f"需求分析超时 (timeout={timeout}s)")
            return {"error": "分析超时"}

    except Exception as e:
        logger.error(f"分析用户需求失败: {str(e)}")
        return {"error": f"分析失败: {str(e)}"}
