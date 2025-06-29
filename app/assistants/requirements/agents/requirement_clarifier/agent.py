"""
需求澄清智能体

负责与用户交互，澄清模糊的需求点，确保需求的完整性和准确性。
支持与其他智能体协作，共享澄清结果。
"""

import asyncio
import json
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agent.base import BaseAgent
from app.assistants.requirements.agents.base_requirements_agent import (
    BaseRequirementsAgent,
)
from app.core.performance_controller import get_performance_controller
from app.core.prompts import REQUIREMENT_CLARIFIER_SYSTEM_PROMPT
from app.core.reflection_engine import ReflectionEngine
from app.core.think_tool import ThinkingPhase, ThinkTool
from app.core.types import AgentState, Message
from app.llm import LLM
from app.logger import get_logger
from app.schema import AgentAction, AgentResponse

from .clarification import RequirementClarification

logger = get_logger(__name__)


class RequirementClarifierAgent(BaseRequirementsAgent):
    """需求澄清智能体"""

    def __init__(self, flow_manager):
        """初始化需求澄清智能体

        Args:
            flow_manager: 工作流管理器
        """
        super().__init__(flow_manager)
        self.llm = LLM()
        self.agent_name = "requirement_clarifier"
        logger.debug(f"需求澄清智能体初始化完成")
        self.clarification_history = []
        self.current_focus = None
        self.collaboration_enabled = True
        self.clarification_tool = RequirementClarification(self.llm)

        # 集成思维工具和反思引擎
        self.think_tool = ThinkTool(llm=self.llm)
        self.reflection_engine = ReflectionEngine(llm=self.llm)

    @get_performance_controller().timeout_control(timeout=30)
    async def quick_analyze(self, requirement: str) -> AgentResponse:
        """
        快速分析模式 - 30秒超时

        Args:
            requirement: 需求文本

        Returns:
            AgentResponse: 智能体响应
        """
        try:
            # 更新状态为运行中
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.RUNNING, task="快速需求分析", progress=0.0
                )

            # 快速思维分析
            thinking_result = await self.think_tool.structured_thinking(
                requirement,
                context={"mode": "quick"},
                phases=[ThinkingPhase.UNDERSTANDING, ThinkingPhase.ANALYSIS],
            )
            logger.info(f"快速思维分析完成，置信度: {thinking_result.confidence:.2f}")

            # 更新进度
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.RUNNING, progress=0.5
                )

            # 简化的澄清
            clarified = {
                "summary": thinking_result.get("summary", ""),
                "key_points": thinking_result.get("insights", [])[:3],
                "recommendations": thinking_result.get("next_actions", [])[:2],
                "confidence": thinking_result.get("confidence", 0.8),
            }

            # 更新状态为完成
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.COMPLETED, task="完成", progress=1.0
                )

            return AgentResponse(
                content=clarified,
                metadata={
                    "mode": "quick",
                    "thinking_summary": thinking_result.get("summary", ""),
                    "confidence": thinking_result.get("confidence", 0.8),
                },
            )

        except Exception as e:
            logger.error(f"快速需求分析失败: {str(e)}")
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.ERROR, task="错误"
                )
            raise

    async def step(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        执行一步澄清操作

        Args:
            input_data: 输入数据，包含：
                - requirement: 需求文本
                - mode: 分析模式 ("quick", "standard", "deep")，默认为"standard"

        Returns:
            AgentResponse: 智能体响应
        """
        try:
            # 获取需要澄清的需求和分析模式
            requirement = input_data.get("requirement", "")
            mode = input_data.get("mode", "standard")

            if not requirement:
                raise ValueError("需求内容不能为空")

            # 快速模式使用专门的处理函数
            if mode == "quick":
                return await self.quick_analyze(requirement)

            # 标准模式
            # 更新状态为运行中
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.RUNNING, task="需求澄清", progress=0.0
                )

            # 使用思维工具进行深度思考
            thinking_result = await self.think_tool.structured_thinking(requirement)
            logger.info(f"思维工具分析完成，置信度: {thinking_result.confidence:.2f}")

            # 执行澄清
            clarified = await self.clarify(requirement)

            # 使用反思引擎评估结果
            reflection_result = await self.reflection_engine.comprehensive_reflection(
                original_input=requirement,
                generated_output=clarified,
                task_description="需求澄清",
                evaluation_criteria=["完整性", "准确性", "清晰度", "一致性"],
            )
            logger.info(
                f"反思引擎评估完成，质量评分: {reflection_result.get('quality_score', 0):.2f}"
            )

            # 更新状态为完成
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.COMPLETED, task="完成", progress=1.0
                )

            return AgentResponse(
                content=clarified,
                metadata={
                    "mode": mode,
                    "clarification_history": self.clarification_history,
                    "thinking_summary": thinking_result.summary,
                    "reflection_insights": reflection_result.get("insights", []),
                },
            )

        except Exception as e:
            logger.error(f"需求分析失败: {str(e)}")
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.ERROR, task="错误"
                )
            raise

    async def clarify_requirements(
        self, requirement: str, knowledge: Dict[str, Any], code_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """澄清需求，提出问题并整理需求

        Args:
            requirement: 原始需求文本
            knowledge: 相关知识库内容
            code_analysis: 相关代码分析结果

        Returns:
            Dict[str, Any]: 澄清结果
        """
        logger.info(f"开始澄清需求: {requirement[:50]}...")

        try:
            # 构建提示词
            prompt = self._build_clarification_prompt(
                requirement, knowledge, code_analysis
            )
            logger.debug("构建提示词完成")

            # 调用LLM
            logger.info("调用LLM进行需求澄清...")
            response = await asyncio.wait_for(self.llm.agenerate(prompt), timeout=30)
            logger.info("LLM调用完成")

            # 解析响应
            clarification_result = self._parse_clarification_response(response)
            logger.info(
                f"需求澄清完成，生成了 {len(clarification_result.get('questions', []))} 个澄清问题"
            )

            return clarification_result
        except asyncio.TimeoutError:
            logger.error("需求澄清LLM调用超时")
            return {
                "error": "LLM调用超时",
                "status": "error",
                "questions": [],
                "summary": "由于LLM调用超时，无法完成需求澄清",
                "clarification_needed": True,
            }
        except Exception as e:
            logger.error(f"需求澄清过程中出现错误: {str(e)}")
            return {
                "error": str(e),
                "status": "error",
                "questions": [],
                "summary": f"需求澄清过程中出现错误: {str(e)}",
                "clarification_needed": True,
            }

    def _build_clarification_prompt(
        self, requirement: str, knowledge: Dict[str, Any], code_analysis: Dict[str, Any]
    ) -> str:
        """构建需求澄清提示词

        Args:
            requirement: 原始需求文本
            knowledge: 相关知识库内容
            code_analysis: 相关代码分析结果

        Returns:
            str: 提示词
        """
        # 提取知识库内容摘要
        knowledge_summary = "\n".join(
            [
                f"- {item.get('title', 'Untitled')}: {item.get('content', '')[:200]}..."
                for item in knowledge.get("results", [])[:3]
            ]
        )

        # 提取代码分析摘要
        code_summary = "\n".join(
            [
                f"- {component.get('name', 'Unknown')}: {component.get('description', '')}"
                for component in code_analysis.get("components", [])[:3]
            ]
        )

        # 构建提示词
        prompt = f"""
你是一位专业的需求分析师，负责澄清和整理软件需求。请分析以下需求，提出澄清问题，并整理需求要点。

## 原始需求
{requirement}

## 相关知识
{knowledge_summary}

## 相关代码组件
{code_summary}

请完成以下任务：
1. 分析需求的完整性、清晰度和一致性
2. 提出5-10个关键澄清问题，这些问题应该能够帮助更好地理解需求
3. 整理需求的主要要点和边界
4. 给出一个结构化的需求摘要

输出格式应为JSON：
```json
{
  "status": "success",
  "questions": [
    {"id": 1, "question": "问题1", "reason": "提问原因"},
    {"id": 2, "question": "问题2", "reason": "提问原因"}
  ],
  "key_points": ["要点1", "要点2", "要点3"],
  "boundaries": ["边界1", "边界2"],
  "summary": "结构化需求摘要",
  "clarification_needed": true/false
}
```

请确保输出是有效的JSON格式。
"""
        return prompt

    def _parse_clarification_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应，提取需求澄清结果

        Args:
            response: LLM响应文本

        Returns:
            Dict[str, Any]: 解析后的澄清结果
        """
        try:
            # 尝试提取JSON部分
            json_str = response

            # 如果响应包含```json和```标记，提取其中的内容
            if "```json" in response and "```" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()

            # 解析JSON
            result = json.loads(json_str)

            # 确保结果包含必要的字段
            if "questions" not in result:
                result["questions"] = []
            if "summary" not in result:
                result["summary"] = "未提供摘要"
            if "clarification_needed" not in result:
                result["clarification_needed"] = len(result["questions"]) > 0
            if "status" not in result:
                result["status"] = "success"

            return result
        except Exception as e:
            logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回一个基本结构
            return {
                "status": "error",
                "error": f"解析响应失败: {str(e)}",
                "questions": [],
                "summary": "无法解析LLM响应",
                "clarification_needed": True,
            }

    async def clarify(self, requirement: str, context: Optional[Dict] = None) -> str:
        """
        执行需求澄清

        Args:
            requirement: 原始需求
            context: 上下文信息

        Returns:
            str: 澄清后的需求
        """
        try:
            # 更新状态为运行中
            if self.flow and self.flow.collaboration_manager:
                try:
                    await self.flow.collaboration_manager.update_state(
                        self.id, state=AgentState.RUNNING, task="需求澄清", progress=0.0
                    )
                except Exception as e:
                    logger.warning(f"状态更新失败（非致命）: {str(e)}")

            # 1. 分析需求
            analysis_result = await self.clarification_tool.analyze_requirement(
                requirement
            )
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.share_data(
                    self.id, "requirement_analysis", analysis_result
                )
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.RUNNING, progress=0.3
                )

            # 2. 识别澄清点
            clarification_points = (
                await self.clarification_tool.identify_clarification_points(
                    analysis_result
                )
            )
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.share_data(
                    self.id, "clarification_points", clarification_points
                )
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.RUNNING, progress=0.6
                )

            # 3. 执行澄清
            clarified_requirement = await self.clarification_tool.execute_clarification(
                requirement, clarification_points, context
            )
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.share_data(
                    self.id, "clarified_requirement", clarified_requirement
                )
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.RUNNING, progress=0.9
                )

            # 4. 验证结果
            final_result = await self.clarification_tool.validate_clarification(
                clarified_requirement
            )
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.COMPLETED, task="完成", progress=1.0
                )

            # 记录历史
            self.clarification_history.append(
                {
                    "type": "clarification",
                    "original": requirement,
                    "clarified": final_result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return final_result

        except Exception as e:
            logger.error(f"需求澄清失败: {str(e)}")
            if self.flow and self.flow.collaboration_manager:
                await self.flow.collaboration_manager.update_state(
                    self.id, AgentState.ERROR, task="错误"
                )
            raise
