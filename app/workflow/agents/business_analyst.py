"""
业务分析师智能体

基于工作流引擎架构，专注于深度业务分析：
- 业务价值分析
- 用户场景建模
- 流程分析
- 风险识别
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from app.llm import LLM
from app.workflow.core.workflow_agent import WorkflowAgent
from app.workflow.core.workflow_context import WorkflowContext
from app.workflow.core.workflow_result import WorkflowResult
from app.workflow.engine.event_bus import EventBus


class BusinessAnalystAgent(WorkflowAgent):
    """业务分析师智能体"""

    def __init__(
        self,
        workflow_context: WorkflowContext,
        event_bus: EventBus,
        name: str = "业务分析师",
        **kwargs,
    ):
        description = "专注于深度业务分析，包括价值分析、场景建模等"
        system_prompt = self._get_system_prompt()

        super().__init__(
            name=name,
            description=description,
            system_prompt=system_prompt,
            workflow_context=workflow_context,
            event_bus=event_bus,
            llm=LLM(config_name="business_analyst"),
            max_steps=3,
            **kwargs,
        )

        self.business_value_score = 0.0
        self.risk_factors: List[str] = []
        self.stakeholders: List[str] = []

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一位经验丰富的业务分析师，专门负责深度分析业务需求和用户场景。

# 核心工作原则
1. **科学严谨**：运用成熟的软件工程需求分析方法
2. **数据驱动**：基于事实和数据进行分析，避免主观臆断
3. **系统思维**：从整体业务价值链角度分析需求
4. **用户中心**：始终以用户价值为分析出发点
5. **可操作性**：分析结果要能指导后续设计和开发

# 专业分析方法
## 1. 业务价值分析（Business Value Analysis）
- **价值主张画布**：核心价值、用户痛点、增值服务
- **商业模式分析**：收入模式、成本结构、关键资源
- **ROI评估**：投资回报率、成本效益分析

## 2. 用户场景建模（User Scenario Modeling）
- **用户画像**：基于真实数据的用户特征分析
- **用户旅程地图**：完整的用户体验流程
- **触点分析**：用户与系统的关键交互点

## 3. 业务流程分析（Business Process Analysis）
- **现状流程**：As-Is流程梳理
- **目标流程**：To-Be流程设计
- **流程优化**：瓶颈识别和改进建议

## 4. 干系人分析（Stakeholder Analysis）
- **利益相关者地图**：内部/外部干系人识别
- **影响力分析**：权力-利益矩阵
- **需求冲突**：不同干系人需求的平衡

## 5. 风险分析（Risk Analysis）
- **业务风险**：市场、竞争、合规风险
- **技术风险**：实现难度、技术选型风险
- **运营风险**：人员、流程、运维风险

请基于以上原则和方法，进行深入的业务分析。"""

    async def step(self, input_data: Any = None) -> Any:
        """执行业务分析步骤"""
        try:
            if self.current_step == 1:
                return await self._analyze_business_value()
            elif self.current_step == 2:
                return await self._analyze_user_scenarios()
            else:
                return await self._generate_analysis_report()

        except Exception as e:
            logger.error(f"业务分析步骤执行失败: {e}")
            raise

    async def _analyze_business_value(self) -> str:
        """分析业务价值"""
        # 从上下文获取澄清后的需求
        requirement_content = self.context.get("requirement_content", "")
        clarification_summary = self.context.get("clarification_summary", "")

        prompt = f"""请分析以下需求的业务价值：

需求内容：
{requirement_content}

需求澄清结果：
{clarification_summary}

分析维度：
1. **核心价值主张**: 解决什么核心问题？
2. **目标用户群体**: 主要服务对象是谁？
3. **业务目标**: 期望达成的业务目标
4. **成功指标**: 如何衡量项目成功？
5. **竞争优势**: 相比现有解决方案的优势

请提供详细的业务价值分析。"""

        response = await self.llm.ask(
            messages=[{"role": "system", "content": prompt}], temperature=0.3
        )

        self.update_memory("assistant", response)

        # 发布业务价值分析完成事件
        await self.event_bus.publish(
            f"{self.name}_business_value_analyzed",
            {"agent": self.name, "analysis": response},
        )

        return response

    async def _analyze_user_scenarios(self) -> str:
        """分析用户场景"""
        prompt = """请分析用户使用场景：

分析内容：
1. **用户角色定义**: 主要用户类型和特征
2. **使用场景**: 典型的使用场景和用户旅程
3. **业务流程**: 核心业务流程的详细步骤
4. **交互点**: 用户与系统的关键交互点
5. **痛点识别**: 当前流程中的问题和痛点

请提供详细的用户场景分析。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.4,
        )

        self.update_memory("assistant", response)

        # 发布用户场景分析完成事件
        await self.event_bus.publish(
            f"{self.name}_user_scenarios_analyzed",
            {"agent": self.name, "analysis": response},
        )

        return response

    async def _generate_analysis_report(self) -> str:
        """生成综合分析报告"""
        prompt = """请基于前面的分析，生成综合业务分析报告：

报告结构：
1. **执行摘要**
2. **业务价值总结**
3. **用户需求洞察**
4. **业务流程建议**
5. **风险评估**
6. **实施建议**
7. **成功指标定义**

请提供完整、专业的业务分析报告。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.3,
        )

        self.update_memory("assistant", response)

        # 更新上下文
        self.context.update(
            {
                "business_analysis_report": response,
                "business_value_score": self.business_value_score,
                "risk_factors": self.risk_factors,
                "stakeholders": self.stakeholders,
            }
        )

        # 发布分析报告完成事件
        await self.event_bus.publish(
            f"{self.name}_analysis_report_generated",
            {
                "agent": self.name,
                "report": response,
                "metadata": self.get_analysis_summary(),
            },
        )

        return response

    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            "business_value_score": self.business_value_score,
            "risk_factors": self.risk_factors,
            "stakeholders": self.stakeholders,
            "current_step": self.current_step,
            "state": self.state.value,
        }
