"""
业务分析师智能体 - 基于BaseAgent

专注于深度业务分析：
- 业务价值分析
- 用户场景建模
- 流程分析
- 风险识别
"""

from typing import Dict, List, Optional

from app.agent.base import BaseAgent
from app.llm import LLM
from app.logger import logger


class BusinessAnalystAgent(BaseAgent):
    """业务分析师智能体"""

    def __init__(self, name: str = "业务分析师", **kwargs):
        system_prompt = self._get_system_prompt()

        super().__init__(
            name=name,
            system_prompt=system_prompt,
            next_step_prompt="请基于澄清后的需求进行深度业务分析。",
            llm=LLM(config_name="business_analyst"),
            max_steps=3,
            **kwargs,
        )

        self.business_value_score = 0.0
        self.risk_factors: List[str] = []
        self.stakeholders: List[str] = []

    def _get_system_prompt(self) -> str:
        """业务分析师系统提示词"""
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

# 分析输出标准
## 结构化分析报告包含：
1. **执行摘要**：核心发现和建议
2. **业务价值分析**：价值主张、商业论证
3. **用户需求洞察**：用户画像、场景分析
4. **业务流程设计**：端到端流程图
5. **干系人影响分析**：关键利益相关者
6. **风险评估矩阵**：风险等级和缓解措施
7. **实施建议**：分阶段实施计划
8. **成功指标**：可量化的KPI定义

# 分析工具运用
- **SWOT分析**：内外部环境分析
- **5W2H分析**：全面问题分析
- **鱼骨图**：问题根因分析
- **优先级矩阵**：重要性-紧急性分析
- **影响分析**：变更影响评估

# 输出格式要求
请按以下结构提供分析：

## 1. 业务价值评估
[基于数据的价值量化分析]

## 2. 用户需求洞察
[用户画像和场景分析]

## 3. 业务流程建议
[优化后的业务流程]

## 4. 关键成功因素
[项目成功的关键要素]

## 5. 风险与缓解
[主要风险和应对策略]

## 6. 实施路径
[分阶段实施建议]

请确保所有分析都基于软件工程最佳实践，具有可操作性和指导价值。"""

    async def step(self) -> str:
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
            return f"业务分析过程中发生错误: {str(e)}"

    async def _analyze_business_value(self) -> str:
        """分析业务价值"""
        prompt = """请分析以下需求的业务价值：

分析维度：
1. **核心价值主张**: 解决什么核心问题？
2. **目标用户群体**: 主要服务对象是谁？
3. **业务目标**: 期望达成的业务目标
4. **成功指标**: 如何衡量项目成功？
5. **竞争优势**: 相比现有解决方案的优势

请提供详细的业务价值分析。"""

        messages = self.memory.get_messages() + [{"role": "system", "content": prompt}]

        response = await self.llm.ask(messages, temperature=0.3)
        self.update_memory("assistant", response)

        logger.info("完成业务价值分析")
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

        messages = self.memory.get_messages() + [{"role": "system", "content": prompt}]

        response = await self.llm.ask(messages, temperature=0.4)
        self.update_memory("assistant", response)

        logger.info("完成用户场景分析")
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

        messages = self.memory.get_messages() + [{"role": "system", "content": prompt}]

        response = await self.llm.ask(messages, temperature=0.3)
        self.update_memory("assistant", response)

        # 设置完成状态
        self.state = self.state.__class__.FINISHED

        logger.info("业务分析报告生成完成")
        return response

    def get_analysis_summary(self) -> Dict:
        """获取分析摘要"""
        return {
            "business_value_score": self.business_value_score,
            "risk_factors": self.risk_factors,
            "stakeholders": self.stakeholders,
            "current_step": self.current_step,
            "state": (
                self.state.value if hasattr(self.state, "value") else str(self.state)
            ),
        }
