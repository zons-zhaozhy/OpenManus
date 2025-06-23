"""
质量评审师智能体 - 专业质量把关

基于软件工程质量保证原则：
- 独立评审：第三方视角评估
- 多维度评审：完整性、正确性、一致性、可行性
- 评审标准：基于行业标准和最佳实践
- 改进建议：具体可操作的优化建议
"""

from typing import Dict, List, Optional

from app.agent.base import BaseAgent
from app.llm import LLM
from app.logger import logger


class QualityReviewerAgent(BaseAgent):
    """质量评审师智能体 - 专业质量把关"""

    def __init__(self, name: str = "质量评审师", **kwargs):
        system_prompt = self._get_system_prompt()

        super().__init__(
            name=name,
            system_prompt=system_prompt,
            next_step_prompt="请对提交的需求分析成果进行专业质量评审。",
            llm=LLM(config_name="quality_reviewer"),
            max_steps=3,
            **kwargs,
        )

        self.review_scores: Dict[str, float] = {}
        self.critical_issues: List[str] = []
        self.improvement_suggestions: List[str] = []

    def _get_system_prompt(self) -> str:
        """质量评审师系统提示词"""
        return """你是一位资深的软件工程质量评审专家，专门负责对需求分析成果进行专业评审和质量把关。

# 核心职责
你是独立的第三方评审者，确保需求分析工作的专业性和质量。

# 评审原则
1. **独立性**：客观中立，不受前期工作影响
2. **专业性**：基于软件工程标准和行业最佳实践
3. **系统性**：全面评估，不遗漏关键要素
4. **建设性**：提出具体可操作的改进建议
5. **严谨性**：严格按照质量标准执行评审

# 评审维度与标准

## 1. 完整性评审 (Completeness Review)
### 需求澄清完整性
- [ ] 核心功能需求是否完整澄清？
- [ ] 非功能需求是否充分识别？
- [ ] 约束条件是否明确定义？
- [ ] 验收标准是否可测试？
- [ ] 关键干系人是否全部识别？

### 业务分析完整性
- [ ] 业务价值是否量化分析？
- [ ] 用户场景是否覆盖完整？
- [ ] 业务流程是否端到端梳理？
- [ ] 风险因素是否全面识别？
- [ ] 实施计划是否具体可行？

### 文档编写完整性
- [ ] 文档结构是否符合标准？
- [ ] 内容是否覆盖所有必要章节？
- [ ] 技术规范是否明确定义？
- [ ] 项目交付物是否清晰列出？

## 2. 正确性评审 (Correctness Review)
- **逻辑一致性**：各部分内容是否逻辑一致？
- **事实准确性**：描述的信息是否准确？
- **技术可行性**：技术方案是否现实可行？
- **业务合理性**：业务逻辑是否合理？

## 3. 清晰性评审 (Clarity Review)
- **表达清晰**：是否用词准确、表达清晰？
- **结构清晰**：文档结构是否层次分明？
- **可理解性**：非技术人员是否能理解？
- **无歧义性**：是否存在多种理解方式？

## 4. 可操作性评审 (Actionability Review)
- **实施指导**：是否提供明确的实施指导？
- **优先级明确**：功能优先级是否清晰？
- **资源需求**：人力、时间、预算需求是否明确？
- **里程碑定义**：关键节点是否可衡量？

## 5. 标准符合性评审 (Standards Compliance)
- **行业标准**：是否符合软件工程行业标准？
- **内部规范**：是否符合组织内部规范？
- **文档模板**：是否按照标准模板编写？
- **最佳实践**：是否体现行业最佳实践？

# 评审流程
## 第一步：初步评审
- 快速浏览全部内容
- 识别明显的缺失和问题
- 评估整体质量水平

## 第二步：详细评审
- 逐项检查评审清单
- 标记具体问题和建议
- 量化评分各个维度

## 第三步：综合评估
- 计算综合质量得分
- 识别关键改进点
- 制定改进建议

# 评审输出格式

## 评审摘要
**整体质量等级**：优秀/良好/合格/需改进/不合格
**综合得分**：X/100分
**主要优点**：[列出2-3个突出优点]
**关键问题**：[列出需要解决的关键问题]

## 详细评审结果

### 1. 各维度评分
- 完整性：X/20分
- 正确性：X/20分
- 清晰性：X/20分
- 可操作性：X/20分
- 标准符合性：X/20分

### 2. 具体问题清单
[按优先级列出具体问题]

### 3. 改进建议
[提供具体可操作的改进建议]

### 4. 风险提醒
[指出可能的项目风险]

### 5. 通过条件
[明确达到通过标准需要满足的条件]

# 评审标准
- **85分以上**：优秀，可直接通过
- **70-84分**：良好，修改后通过
- **60-69分**：合格，需要改进
- **60分以下**：不合格，需要重做

严格按照以上标准执行评审，确保需求分析工作的专业性和质量。"""

    async def step(self) -> str:
        """执行质量评审步骤"""
        try:
            if self.current_step == 1:
                return await self._initial_review()
            elif self.current_step == 2:
                return await self._detailed_review()
            else:
                return await self._final_assessment()

        except Exception as e:
            logger.error(f"质量评审步骤执行失败: {e}")
            return f"质量评审过程中发生错误: {str(e)}"

    async def _initial_review(self) -> str:
        """初步评审"""
        prompt = """请对提交的需求分析成果进行初步评审：

评审要点：
1. **整体结构**：文档结构是否完整合理？
2. **内容覆盖**：是否覆盖了需求分析的各个方面？
3. **明显缺失**：是否存在明显的内容缺失？
4. **质量水平**：初步判断整体质量水平

请提供初步评审意见，识别需要重点关注的领域。"""

        messages = self.memory.get_messages() + [{"role": "system", "content": prompt}]

        response = await self.llm.ask(messages, temperature=0.2)
        self.update_memory("assistant", response)

        logger.info("完成初步质量评审")
        return response

    async def _detailed_review(self) -> str:
        """详细评审"""
        prompt = """请进行详细的质量评审：

按照评审清单逐项检查：
1. **完整性评审**：内容是否完整？
2. **正确性评审**：信息是否准确？
3. **清晰性评审**：表达是否清晰？
4. **可操作性评审**：是否具有指导价值？
5. **标准符合性**：是否符合行业标准？

请为每个维度打分（1-20分），并指出具体问题。"""

        messages = self.memory.get_messages() + [{"role": "system", "content": prompt}]

        response = await self.llm.ask(messages, temperature=0.3)
        self.update_memory("assistant", response)

        # 解析评分
        self._extract_scores(response)

        logger.info("完成详细质量评审")
        return response

    async def _final_assessment(self) -> str:
        """最终评估"""
        prompt = """请基于前面的评审，提供最终综合评估：

输出内容：
1. **评审摘要**：整体质量等级和综合得分
2. **主要优点**：值得肯定的方面
3. **关键问题**：必须解决的问题
4. **改进建议**：具体可操作的建议
5. **通过建议**：是否建议通过评审

请给出明确的评审结论和后续行动建议。"""

        messages = self.memory.get_messages() + [{"role": "system", "content": prompt}]

        response = await self.llm.ask(messages, temperature=0.2)
        self.update_memory("assistant", response)

        # 设置完成状态
        self.state = self.state.__class__.FINISHED

        logger.info("质量评审完成")
        return response

    def _extract_scores(self, response: str):
        """从评审结果中提取评分"""
        # 简单的评分提取逻辑
        import re

        # 提取各维度评分
        dimensions = ["完整性", "正确性", "清晰性", "可操作性", "标准符合性"]
        for dim in dimensions:
            pattern = f"{dim}[：:]\s*(\d+)"
            match = re.search(pattern, response)
            if match:
                self.review_scores[dim] = float(match.group(1))

    def get_review_summary(self) -> Dict:
        """获取评审摘要"""
        total_score = sum(self.review_scores.values()) if self.review_scores else 0

        return {
            "total_score": total_score,
            "dimension_scores": self.review_scores,
            "critical_issues_count": len(self.critical_issues),
            "improvement_suggestions_count": len(self.improvement_suggestions),
            "current_step": self.current_step,
            "state": (
                self.state.value if hasattr(self.state, "value") else str(self.state)
            ),
            "quality_level": self._get_quality_level(total_score),
        }

    def _get_quality_level(self, score: float) -> str:
        """根据得分确定质量等级"""
        if score >= 85:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 60:
            return "合格"
        else:
            return "需改进"
