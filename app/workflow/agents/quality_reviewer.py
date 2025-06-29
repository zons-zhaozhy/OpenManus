"""
质量审查智能体

负责对需求分析过程和文档进行全方位质量审查：
- 需求完整性
- 一致性
- 可追溯性
- 可测试性
- 规范性
"""

from typing import Any, Dict, List, Optional
from enum import Enum

from loguru import logger

from app.workflow.core.workflow_agent import WorkflowAgent
from app.workflow.core.workflow_context import WorkflowContext
from app.workflow.core.workflow_result import WorkflowResult
from app.workflow.engine.event_bus import EventBus
from app.llm import LLM


class ReviewDimension(Enum):
    """审查维度"""
    COMPLETENESS = "完整性"
    CONSISTENCY = "一致性"
    TRACEABILITY = "可追溯性"
    TESTABILITY = "可测试性"
    COMPLIANCE = "规范性"


class QualityReviewerAgent(WorkflowAgent):
    """质量审查智能体"""

    def __init__(
        self,
        workflow_context: WorkflowContext,
        event_bus: EventBus,
        name: str = "质量审查专家",
        **kwargs
    ):
        description = "负责对需求分析过程和文档进行全方位质量审查"
        system_prompt = self._get_system_prompt()

        super().__init__(
            name=name,
            description=description,
            system_prompt=system_prompt,
            workflow_context=workflow_context,
            event_bus=event_bus,
            llm=LLM(config_name="quality_reviewer"),
            max_steps=5,
            **kwargs
        )

        self.current_dimension = ReviewDimension.COMPLETENESS
        self.review_scores = {dim: 0.0 for dim in ReviewDimension}
        self.review_comments: Dict[ReviewDimension, str] = {}
        self.overall_quality_score = 0.0

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一位专业的需求质量审查专家，负责确保需求分析过程和文档的质量。

# 工作原则
1. **客观公正**：基于事实和标准进行评估
2. **全面系统**：覆盖所有质量维度
3. **问题导向**：及时发现并指出问题
4. **建设性**：提供具体的改进建议

# 审查维度
## 1. 完整性
- 需求覆盖度
- 细节完备性
- 边界条件
- 异常处理

## 2. 一致性
- 术语统一
- 逻辑一致
- 格式规范
- 版本一致

## 3. 可追溯性
- 需求来源
- 变更历史
- 关联关系
- 影响分析

## 4. 可测试性
- 明确性
- 可验证性
- 测试条件
- 验收标准

## 5. 规范性
- 文档标准
- 描述规范
- 格式要求
- 命名规则

请基于以上原则和维度，进行严格的质量审查。"""

    async def step(self, input_data: Any = None) -> Any:
        """执行审查步骤"""
        try:
            if self.current_step == 1:
                return await self._prepare_review_context()
            elif self.current_step == 2:
                return await self._review_current_dimension()
            elif self.current_step == 3:
                return await self._analyze_review_results()
            elif self.current_step == 4:
                return await self._generate_improvement_suggestions()
            else:
                return await self._summarize_review()

        except Exception as e:
            logger.error(f"质量审查步骤执行失败: {e}")
            raise

    async def _prepare_review_context(self) -> str:
        """准备审查上下文"""
        # 从工作流上下文获取需要审查的内容
        requirement_content = self.context.get("requirement_content", "")
        clarification_results = self.context.get("clarification_results", "")
        business_analysis = self.context.get("business_analysis", "")
        technical_docs = self.context.get("technical_docs", "")

        prompt = f"""请准备对以下内容进行{self.current_dimension.value}审查：

需求内容：
{requirement_content}

需求澄清结果：
{clarification_results}

业务分析：
{business_analysis}

技术文档：
{technical_docs}

请提供审查准备工作的总结。"""

        response = await self.llm.ask(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3
        )
        
        self.update_memory("assistant", response)
        
        # 发布审查准备完成事件
        await self.event_bus.publish(
            f"{self.name}_review_prepared",
            {
                "agent": self.name,
                "dimension": self.current_dimension.value,
                "preparation": response
            }
        )
        
        return response

    async def _review_current_dimension(self) -> str:
        """执行当前维度的审查"""
        prompt = f"""请对当前维度（{self.current_dimension.value}）进行详细审查：

审查要点：
1. 优势和亮点
2. 存在的问题
3. 潜在的风险
4. 改进空间

请提供详细的审查报告。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.3
        )
        
        self.update_memory("assistant", response)
        
        # 保存审查评论
        self.review_comments[self.current_dimension] = response
        
        # 计算当前维度的分数
        self.review_scores[self.current_dimension] = self._calculate_dimension_score(response)
        
        # 发布维度审查完成事件
        await self.event_bus.publish(
            f"{self.name}_dimension_reviewed",
            {
                "agent": self.name,
                "dimension": self.current_dimension.value,
                "review": response,
                "score": self.review_scores[self.current_dimension]
            }
        )
        
        return response

    async def _analyze_review_results(self) -> str:
        """分析审查结果"""
        prompt = """请分析所有维度的审查结果：

分析要点：
1. 各维度评分对比
2. 主要问题汇总
3. 改进优先级
4. 整体质量评估

请提供详细的分析报告。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.3
        )
        
        self.update_memory("assistant", response)
        
        # 计算整体质量分数
        self.overall_quality_score = sum(self.review_scores.values()) / len(self.review_scores)
        
        # 发布分析完成事件
        await self.event_bus.publish(
            f"{self.name}_results_analyzed",
            {
                "agent": self.name,
                "analysis": response,
                "overall_score": self.overall_quality_score
            }
        )
        
        return response

    async def _generate_improvement_suggestions(self) -> str:
        """生成改进建议"""
        prompt = """请基于审查结果生成具体的改进建议：

建议要求：
1. 针对性：对应具体问题
2. 可行性：切实可执行
3. 优先级：重要紧急度
4. 效果：预期改进效果

请提供详细的改进建议。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.3
        )
        
        self.update_memory("assistant", response)
        
        # 发布改进建议事件
        await self.event_bus.publish(
            f"{self.name}_improvements_suggested",
            {
                "agent": self.name,
                "suggestions": response
            }
        )
        
        return response

    async def _summarize_review(self) -> str:
        """总结审查结果"""
        prompt = """请对整个质量审查过程进行总结：

总结要点：
1. 总体质量评估
2. 关键发现
3. 主要建议
4. 后续行动

请提供完整的审查总结报告。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.3
        )
        
        self.update_memory("assistant", response)
        
        # 更新上下文
        self.context.update({
            "quality_review_summary": response,
            "quality_scores": self.review_scores,
            "overall_quality_score": self.overall_quality_score
        })
        
        # 发布总结完成事件
        await self.event_bus.publish(
            f"{self.name}_review_summarized",
            {
                "agent": self.name,
                "summary": response,
                "scores": {dim.value: score for dim, score in self.review_scores.items()},
                "overall_score": self.overall_quality_score
            }
        )
        
        return response

    def _calculate_dimension_score(self, review_content: str) -> float:
        """计算维度得分"""
        score = 0.0
        positive_indicators = [
            "完整", "清晰", "准确", "规范", "合理",
            "充分", "详细", "严谨", "专业", "优秀"
        ]
        negative_indicators = [
            "缺失", "混乱", "模糊", "不规范", "不合理",
            "不足", "粗糙", "随意", "业余", "差"
        ]
        
        for indicator in positive_indicators:
            if indicator in review_content:
                score += 1.0
                
        for indicator in negative_indicators:
            if indicator in review_content:
                score -= 1.0
        
        # 归一化到0-10分
        total_indicators = len(positive_indicators) + len(negative_indicators)
        normalized_score = (score + total_indicators) / (2 * total_indicators) * 10
        
        return round(normalized_score, 2)

    async def switch_dimension(self) -> None:
        """切换审查维度"""
        dimensions = list(ReviewDimension)
        current_index = dimensions.index(self.current_dimension)
        next_index = (current_index + 1) % len(dimensions)
        self.current_dimension = dimensions[next_index]
        
        # 重置步骤
        self.current_step = 1
        
        # 发布维度切换事件
        await self.event_bus.publish(
            f"{self.name}_dimension_switched",
            {
                "agent": self.name,
                "old_dimension": dimensions[current_index].value,
                "new_dimension": dimensions[next_index].value
            }
        )

    def get_review_summary(self) -> Dict[str, Any]:
        """获取审查摘要"""
        return {
            "current_dimension": self.current_dimension.value,
            "dimension_scores": {
                dim.value: score 
                for dim, score in self.review_scores.items()
            },
            "overall_score": self.overall_quality_score,
            "current_step": self.current_step,
            "state": self.state.value
        }
