"""
需求澄清智能体

负责需求的初步分析和澄清，通过多轮对话引导用户完善需求。
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agent.base import BaseAgent
from app.assistants.requirements.agents.base_requirements_agent import (
    BaseRequirementsAgent,
)
from app.core import config
from app.llm import LLM, get_llm_client
from app.logger import get_logger
from app.tool.base import BaseTool
from app.tool import ToolCode

logger = get_logger(__name__)


class RequirementClarifier(BaseRequirementsAgent):
    """需求澄清智能体类"""

    def __init__(self):
        super().__init__("requirement_clarifier")
        self.llm = get_llm_client()

    async def _analyze(
        self, requirement_text: str, shared_context: Dict[str, Any], **kwargs
    ) -> Dict:
        """
        分析需求并生成澄清问题

        Args:
            requirement_text: 需求文本
            shared_context: 共享上下文
            **kwargs: 额外参数

        Returns:
            Dict: 分析结果，包含澄清问题等
        """
        try:
            # 1. 初步分析需求 (必须首先完成)
            logger.debug(f"[{self.agent_id}] 开始初步分析需求...")
            initial_analysis = await self._initial_analysis(requirement_text)
            logger.debug(
                f"[{self.agent_id}] 初步分析完成，结果: {initial_analysis.get('summary', initial_analysis)[:100]}..."
            )

            # 2. 并行生成澄清问题、评估完整性和识别潜在风险
            logger.debug(
                f"[{self.agent_id}] 并行执行澄清问题生成、完整性评估和风险识别..."
            )
            (clarification_questions, completeness_score, risks) = await asyncio.gather(
                self._generate_questions(requirement_text, initial_analysis),
                self._assess_completeness(requirement_text, initial_analysis),
                self._identify_risks(requirement_text, initial_analysis),
            )
            logger.debug(
                f"[{self.agent_id}] 并行任务完成：澄清问题数量={len(clarification_questions)}, 完整性评分={completeness_score.get('overall_score', 'N/A')}, 风险数量={len(risks)}"
            )

            # 构建结果
            result = {
                "timestamp": datetime.now().isoformat(),
                "requirement_text": requirement_text,
                "initial_analysis": initial_analysis,
                "clarification_questions": clarification_questions,
                "completeness_score": completeness_score,
                "risks": risks,
                "summary": initial_analysis.get("summary", ""),
                "status": "需要澄清" if clarification_questions else "完整",
            }
            logger.info(
                f"[{self.agent_id}] 需求澄清智能体分析完成。状态: {result['status']}"
            )

            return result

        except Exception as e:
            logger.error(f"[{self.agent_id}] 需求分析失败: {str(e)}", exc_info=True)
            raise

    async def _initial_analysis(self, requirement_text: str) -> Dict:
        """初步分析需求"""
        try:
            # 使用LLM进行初步分析
            prompt = f"""
            请对以下需求进行初步分析：

            {requirement_text}

            请从以下几个方面进行分析：
            1. 需求的主要目标
            2. 关键功能点
            3. 约束条件
            4. 用户价值
            5. 技术可行性

            输出格式要求：
            {{
                "main_goal": "主要目标",
                "key_features": ["功能点1", "功能点2", ...],
                "constraints": ["约束1", "约束2", ...],
                "user_value": "用户价值描述",
                "technical_feasibility": "技术可行性分析",
                "summary": "总体概述"
            }}
            """

            response = await self.llm.analyze(prompt)
            return response

        except Exception as e:
            logger.error(f"初步分析失败: {str(e)}")
            raise

    async def _generate_questions(
        self, requirement_text: str, initial_analysis: Dict
    ) -> List[Dict]:
        """生成澄清问题"""
        try:
            # 使用LLM生成澄清问题
            prompt = f"""
            基于以下需求和初步分析，生成需要澄清的问题：

            需求：
            {requirement_text}

            初步分析：
            {initial_analysis}

            请生成具体、有针对性的问题，帮助更好地理解和完善需求。
            每个问题都应该：
            1. 明确指出不清晰或缺失的信息
            2. 有助于细化需求
            3. 便于用户回答

            输出格式：
            [
                {{
                    "question": "问题内容",
                    "purpose": "提问目的",
                    "category": "问题类别",
                    "priority": "优先级(1-5)"
                }},
                ...
            ]
            """

            response = await self.llm.analyze(prompt)
            return response

        except Exception as e:
            logger.error(f"生成澄清问题失败: {str(e)}")
            raise

    async def _assess_completeness(
        self, requirement_text: str, initial_analysis: Dict
    ) -> Dict:
        """评估需求完整性"""
        try:
            # 使用LLM评估完整性
            prompt = f"""
            请评估以下需求的完整性：

            需求：
            {requirement_text}

            初步分析：
            {initial_analysis}

            请从以下维度进行评分（0-100）并给出评分理由：
            1. 目标清晰度
            2. 功能完整性
            3. 约束明确性
            4. 可验证性
            5. 可实现性

            输出格式：
            {{
                "scores": {{
                    "goal_clarity": 分数,
                    "functional_completeness": 分数,
                    "constraint_clarity": 分数,
                    "verifiability": 分数,
                    "feasibility": 分数
                }},
                "reasons": {{
                    "goal_clarity": "评分理由",
                    "functional_completeness": "评分理由",
                    "constraint_clarity": "评分理由",
                    "verifiability": "评分理由",
                    "feasibility": "评分理由"
                }},
                "overall_score": 总分,
                "summary": "总体评价"
            }}
            """

            response = await self.llm.analyze(prompt)
            return response

        except Exception as e:
            logger.error(f"评估完整性失败: {str(e)}")
            raise

    async def _identify_risks(
        self, requirement_text: str, initial_analysis: Dict
    ) -> List[Dict]:
        """识别潜在风险"""
        try:
            # 使用LLM识别风险
            prompt = f"""
            请识别以下需求中的潜在风险：

            需求：
            {requirement_text}

            初步分析：
            {initial_analysis}

            请从以下方面识别风险：
            1. 技术风险
            2. 业务风险
            3. 项目管理风险
            4. 用户体验风险
            5. 安全风险

            输出格式：
            [
                {{
                    "risk_type": "风险类型",
                    "description": "风险描述",
                    "impact": "影响程度(1-5)",
                    "probability": "发生概率(1-5)",
                    "mitigation": "建议的缓解措施"
                }},
                ...
            ]
            """

            response = await self.llm.analyze(prompt)
            return response

        except Exception as e:
            logger.error(f"识别风险失败: {str(e)}")
            raise

    async def clarify_requirements(
        self,
        requirement: str,
        knowledge: Dict[str, Any],
        code_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """外部调用的澄清需求接口"""
        logger.info(f"[{self.agent_id}] 开始澄清需求...")
        # 在这里可以根据知识和代码分析来调整澄清策略或生成更精准的问题
        # 目前简化处理，直接调用_analyze
        analysis_result = await self._analyze(requirement, {})

        # 根据分析结果生成最终的澄清输出
        # 这里可以加入更多逻辑，例如过滤问题，优先显示高优先级问题等
        final_clarification = {
            "summary": analysis_result.get("summary", ""),
            "clarification_needed": analysis_result["status"] == "需要澄清",
            "questions": analysis_result.get("clarification_questions", []),
            "risks": analysis_result.get("risks", []),
            "completeness_score": analysis_result.get("completeness_score", {}),
        }

        logger.info(
            f"[{self.agent_id}] 需求澄清完成。状态: {analysis_result['status']}"
        )
        return final_clarification


class RequirementClarifierAgent(BaseRequirementsAgent):
    """需求澄清智能体 (代理) 的实际实现"""

    def __init__(self, flow: Any):  # Use Any to avoid circular dependency
        super().__init__("clarifier")
        self.flow = flow
        self.clarifier_logic = RequirementClarifier()
        logger.info(f"[{self.agent_id}] RequirementClarifierAgent 初始化完成")

    async def step(self, input_text: str) -> Dict[str, Any]:
        """
        执行需求澄清步骤

        Args:
            input_text: 初始需求文本

        Returns:
            Dict[str, Any]: 澄清结果
        """
        logger.info(f"[{self.agent_id}] 收到需求: {input_text[:50]}...")
        # 这里应该从flow获取contextual knowledge和code_analysis
        # 暂时使用空的字典作为占位符
        knowledge = {}
        code_analysis = {}

        # 调用底层的澄清逻辑
        clarification_result = await self.clarifier_logic.clarify_requirements(
            input_text, knowledge, code_analysis
        )

        logger.info(f"[{self.agent_id}] 需求澄清完成。")
        return clarification_result
