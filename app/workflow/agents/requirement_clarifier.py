"""
需求澄清智能体

基于工作流引擎架构，负责通过智能对话澄清用户的模糊需求，
提出关键问题，引导用户明确表达需求的核心要素。
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from app.llm import LLM
from app.workflow.core.workflow_agent import WorkflowAgent
from app.workflow.core.workflow_context import WorkflowContext
from app.workflow.core.workflow_result import WorkflowResult
from app.workflow.engine.event_bus import EventBus


class RequirementDimension(Enum):
    """需求维度"""

    FUNCTIONAL = "功能需求"
    NON_FUNCTIONAL = "非功能需求"
    BUSINESS = "业务目标"
    CONSTRAINTS = "约束条件"
    RISKS = "风险点"


class RequirementClarifierAgent(WorkflowAgent):
    """需求澄清智能体"""

    def __init__(
        self,
        workflow_context: WorkflowContext,
        event_bus: EventBus,
        name: str = "需求澄清师",
        **kwargs,
    ):
        description = "负责澄清模糊的用户需求，提出关键问题"
        system_prompt = self._get_system_prompt()

        super().__init__(
            name=name,
            description=description,
            system_prompt=system_prompt,
            workflow_context=workflow_context,
            event_bus=event_bus,
            llm=LLM(config_name="requirement_clarifier"),
            max_steps=3,
            **kwargs,
        )

        self.current_dimension = RequirementDimension.FUNCTIONAL
        self.quality_scores = {dim: 0.0 for dim in RequirementDimension}
        self.unclear_points: List[str] = []
        self.questions: List[str] = []

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的需求分析专家，负责通过智能对话澄清用户的模糊需求。

# 工作职责
1. 分析需求中的不明确之处
2. 提出有针对性的澄清问题
3. 引导用户明确表达需求
4. 确保需求的完整性和准确性

# 工作方法
1. 多维度分析
   - 功能需求
   - 非功能需求
   - 业务目标
   - 约束条件
   - 风险点

2. 系统性思维
   - 全局视角
   - 逻辑性强
   - 结构化分析

3. 专业化沟通
   - 准确表达
   - 有效引导
   - 及时反馈

# 输出要求
1. 明确的问题列表
2. 结构化的分析结果
3. 可操作的建议
4. 清晰的优先级

请基于以上原则，帮助用户澄清需求。"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行需求澄清任务"""
        try:
            # 获取输入数据
            initial_analysis = input_data.get("initial_analysis_result")
            requirement_points = input_data.get("requirement_points", [])

            if not initial_analysis:
                raise ValueError("缺少初步分析结果")

            # 执行所有步骤
            for step in range(1, self.max_steps + 1):
                self.current_step = step
                result = await self.step(input_data)
                self.context.update(result)

            # 返回最终结果
            return {
                "clarified_requirements": self.context.get(
                    "clarified_requirements", ""
                ),
                "clarification_questions": self.questions,
                "unclear_points": self.unclear_points,
                "quality_scores": self.quality_scores,
                "current_dimension": self.current_dimension.value,
            }

        except Exception as e:
            logger.error(f"需求澄清执行失败: {e}")
            raise

    async def step(self, input_data: Any = None) -> Any:
        """执行需求澄清步骤"""
        try:
            if self.current_step == 1:
                return await self._analyze_current_dimension(input_data)
            elif self.current_step == 2:
                return await self._generate_questions()
            else:
                return await self._summarize_clarification()

        except Exception as e:
            logger.error(f"需求澄清步骤执行失败: {e}")
            raise

    async def _analyze_current_dimension(self, content: Optional[str]) -> str:
        """分析当前维度的需求"""
        if content is None:
            # 从上下文中获取需求内容
            content = self.context.get("requirement_content", "")
            if not content:
                raise ValueError("No requirement content found in context")

        prompt = f"""请分析以下需求中关于{self.current_dimension.value}的部分：

{content}

分析要点：
1. 是否明确完整？
2. 是否存在歧义？
3. 是否有遗漏的关键信息？
4. 是否需要进一步澄清？

请提供详细分析。"""

        response = await self.llm.ask(
            messages=[{"role": "system", "content": prompt}], temperature=0.3
        )

        self.update_memory("assistant", response)
        return response

    async def _generate_questions(self) -> str:
        """生成澄清问题"""
        prompt = """基于前面的分析，请生成具体的澄清问题：

问题要求：
1. 明确具体
2. 有针对性
3. 易于回答
4. 符合当前维度

请提供优先级排序的问题列表。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.4,
        )

        # 解析并存储问题
        self._extract_questions(response)

        self.update_memory("assistant", response)
        return response

    async def _summarize_clarification(self) -> str:
        """总结澄清结果"""
        prompt = """请总结本轮需求澄清的结果：

总结内容：
1. 已经明确的部分
2. 仍需澄清的问题
3. 潜在风险点
4. 下一步建议

请提供结构化的总结报告。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.3,
        )

        self.update_memory("assistant", response)

        # 更新上下文
        self.context.update(
            {
                "clarification_summary": response,
                "clarification_questions": self.questions,
                "unclear_points": self.unclear_points,
                "quality_scores": self.quality_scores,
            }
        )

        return response

    def _extract_questions(self, response: str) -> None:
        """从回复中提取问题"""
        # 简单的问题提取逻辑
        lines = response.split("\n")
        for line in lines:
            if "?" in line:
                self.questions.append(line.strip())

    def get_clarification_summary(self) -> Dict[str, Any]:
        """获取澄清总结"""
        return {
            "dimension": self.current_dimension.value,
            "quality_scores": self.quality_scores,
            "questions_count": len(self.questions),
            "unclear_points_count": len(self.unclear_points),
            "current_step": self.current_step,
            "state": self.state.value,
        }

    async def switch_dimension(self) -> None:
        """切换需求维度"""
        dimensions = list(RequirementDimension)
        current_index = dimensions.index(self.current_dimension)
        next_index = (current_index + 1) % len(dimensions)
        self.current_dimension = dimensions[next_index]

        # 发布维度切换事件
        await self.event_bus.publish(
            f"{self.name}_dimension_switched",
            {
                "agent": self.name,
                "old_dimension": dimensions[current_index].value,
                "new_dimension": dimensions[next_index].value,
            },
        )
