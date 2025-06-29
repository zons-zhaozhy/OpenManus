"""
需求分析智能体

基于工作流引擎架构，负责分析和理解用户的初始需求，
提取关键信息，识别需求要点。
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from app.llm import LLM
from app.workflow.core.workflow_agent import WorkflowAgent
from app.workflow.core.workflow_context import WorkflowContext
from app.workflow.core.workflow_result import WorkflowResult
from app.workflow.engine.event_bus import EventBus


class RequirementsAnalyzerAgent(WorkflowAgent):
    """需求分析智能体"""

    def __init__(
        self,
        workflow_context: WorkflowContext,
        event_bus: EventBus,
        name: str = "需求分析师",
        **kwargs,
    ):
        description = "负责分析和理解用户的初始需求"
        system_prompt = self._get_system_prompt()

        super().__init__(
            name=name,
            description=description,
            system_prompt=system_prompt,
            workflow_context=workflow_context,
            event_bus=event_bus,
            llm=LLM(config_name="requirements_analyzer"),
            max_steps=3,
            **kwargs,
        )

        self.requirement_points: List[str] = []
        self.analysis_depth = 0.0
        self.completeness_score = 0.0

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的需求分析师，负责分析和理解用户的初始需求。

# 工作职责
1. 深入理解用户需求
2. 提取关键需求点
3. 识别潜在风险
4. 评估需求完整性
5. 提出澄清建议

# 工作方法
1. 系统性分析
   - 全局视角
   - 逻辑性强
   - 结构化思维

2. 重点关注
   - 功能需求
   - 非功能需求
   - 业务目标
   - 技术约束
   - 质量要求

3. 输出要求
   - 清晰的需求要点
   - 完整的分析结果
   - 具体的澄清问题
   - 风险提示

请基于以上原则，帮助分析用户需求。"""

    async def step(self, input_data: Any = None) -> Any:
        """执行需求分析步骤"""
        try:
            logger.info(f"[{self.name}] 开始执行步骤 {self.current_step}...")
            if self.current_step == 1:
                result = await self._analyze_initial_requirements(input_data)
                logger.debug(f"[{self.name}] 步骤 1 (初始分析) 完成。结果摘要: {result.get('initial_analysis_result', '')[:100]}...")
                return result
            elif self.current_step == 2:
                result = await self._extract_requirement_points()
                logger.debug(f"[{self.name}] 步骤 2 (提取要点) 完成。提取要点数量: {len(self.requirement_points)}")
                return result
            else:
                result = await self._generate_clarification_questions()
                logger.debug(f"[{self.name}] 步骤 3 (生成澄清问题) 完成。澄清问题数量: {len(result.get('clarification_questions', []))}")
                return result

        except Exception as e:
            logger.error(f"[{self.name}] 需求分析步骤执行失败: {e}", exc_info=True)
            raise

    async def _analyze_initial_requirements(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析初始需求"""
        logger.debug(f"[{self.name}] 开始分析初始需求...")
        initial_requirements = input_data.get("initial_requirements", "")
        project_context = input_data.get("project_context", "")
        logger.debug(f"[{self.name}] 初始需求输入: {initial_requirements[:100]}..., 项目上下文: {project_context}")

        prompt = f"""请分析以下初始需求和项目上下文：

初始需求：
{initial_requirements}

项目上下文：
{project_context}

请提供：
1. 需求的主要目标
2. 关键功能点
3. 非功能性需求
4. 潜在风险点
5. 需要澄清的问题

进行深入的分析并提供详细的结果。"""

        response = await self.llm.ask(
            messages=[{"role": "system", "content": prompt}], temperature=0.3
        )
        logger.debug(f"[{self.name}] 初始需求分析LLM响应: {response[:100]}...")

        self.update_memory("assistant", response)
        self.analysis_depth = 0.4
        logger.debug(f"[{self.name}] 初始需求分析完成。分析深度: {self.analysis_depth}")

        return {
            "initial_analysis_result": response,
            "analysis_depth": self.analysis_depth,
        }

    async def _extract_requirement_points(self) -> Dict[str, Any]:
        """提取需求要点"""
        logger.debug(f"[{self.name}] 开始提取需求要点...")
        # 获取之前的分析结果
        analysis_result = self.context.get("initial_analysis_result", "")
        logger.debug(f"[{self.name}] 基于分析结果提取要点: {analysis_result[:100]}...")

        prompt = f"""基于之前的分析结果，请提取具体的需求要点：

分析结果：
{analysis_result}

请列出：
1. 具体的功能需求点
2. 非功能性需求要求
3. 业务规则和约束
4. 技术要求和限制
5. 质量标准

请以结构化的方式提供这些要点。"""

        response = await self.llm.ask(
            messages=[{"role": "system", "content": prompt}], temperature=0.3
        )
        logger.debug(f"[{self.name}] 提取要点LLM响应: {response[:100]}...")

        self.update_memory("assistant", response)
        self.requirement_points = response.split("\n")
        self.analysis_depth = 0.7
        logger.debug(f"[{self.name}] 需求要点提取完成。要点数量: {len(self.requirement_points)}, 分析深度: {self.analysis_depth}")

        return {
            "requirement_points": self.requirement_points,
            "analysis_depth": self.analysis_depth,
        }

    async def _generate_clarification_questions(self) -> Dict[str, Any]:
        """生成澄清问题"""
        logger.debug(f"[{self.name}] 开始生成澄清问题...")
        # 获取之前的分析结果和需求要点
        analysis_result = self.context.get("initial_analysis_result", "")
        requirement_points = self.context.get("requirement_points", [])
        logger.debug(f"[{self.name}] 基于分析结果和要点生成澄清问题。分析结果摘要: {analysis_result[:100]}..., 要点数量: {len(requirement_points)}")

        prompt = (
            "基于之前的分析和需求要点，请生成需要澄清的问题：\n\n"
            "分析结果：\n"
            f"{analysis_result}\n\n"
            "需求要点：\n"
            f"{chr(10).join(requirement_points)}\n\n"
            "请生成：\n"
            "1. 关键澄清问题\n"
            "2. 细节确认问题\n"
            "3. 边界条件问题\n"
            "4. 约束条件问题\n"
            "5. 优先级问题\n\n"
            "请确保问题具体、清晰、有针对性。"
        )

        response = await self.llm.ask(
            messages=[{"role": "system", "content": prompt}], temperature=0.3
        )
        logger.debug(f"[{self.name}] 生成澄清问题LLM响应: {response[:100]}...")

        self.update_memory("assistant", response)
        self.analysis_depth = 1.0
        self.completeness_score = 0.8
        logger.info(f"[{self.name}] 澄清问题生成完成。问题数量: {len(response.split('\n'))}, 分析深度: {self.analysis_depth}, 完整性评分: {self.completeness_score}")

        return {
            "clarification_questions": response.split("\n"),
            "analysis_depth": self.analysis_depth,
            "completeness_score": self.completeness_score,
        }

    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            "requirement_points": self.requirement_points,
            "analysis_depth": self.analysis_depth,
            "completeness_score": self.completeness_score,
            "memory": self.memory,
        }
