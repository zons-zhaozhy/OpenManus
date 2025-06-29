"""
需求分析流程的质量控制模块
"""

from typing import Dict, List, Optional

from app.core.types import AgentState
from app.logger import logger

from ..core.base import BaseRequirementsFlow


class QualityController:
    """质量控制器"""

    def __init__(self, flow: BaseRequirementsFlow):
        self.flow = flow

    async def _quality_review_enhanced(self, documentation_result: str) -> str:
        """增强的质量评审流程"""
        logger.info("开始质量评审流程")

        reviewer = self.flow.agents["reviewer"]
        await self.flow.collaboration_manager.update_state(
            reviewer.id, AgentState.WORKING, task="质量评审"
        )

        # 准备评审材料
        review_materials = await self._prepare_quality_review(documentation_result)

        # 分析潜在问题
        potential_issues = await self._analyze_potential_issues(documentation_result)

        # 执行质量评审
        review_result = await reviewer.review_requirements(
            documentation_result,
            review_materials,
            potential_issues,
            self.flow.knowledge_base.get_relevant_knowledge(),
        )

        await self.flow.collaboration_manager.update_state(
            reviewer.id, AgentState.COMPLETED, task="质量评审完成"
        )

        return review_result

    async def _prepare_quality_review(self, analysis_result: str) -> str:
        """准备质量评审材料"""
        # 收集评审所需的上下文信息
        review_context = {
            "original_input": self.flow.state_manager.get_data("user_input"),
            "clarification_result": self.flow.current_context.get(
                "clarification_result"
            ),
            "analysis_result": analysis_result,
            "knowledge_base_data": self.flow.knowledge_base.get_relevant_knowledge(),
            "code_analysis_data": self.flow.code_analyzer.get_analysis_results(),
        }

        # 格式化评审材料
        review_materials = (
            f"原始需求:\n{review_context['original_input']}\n\n"
            f"需求澄清结果:\n{review_context['clarification_result']}\n\n"
            f"分析结果:\n{review_context['analysis_result']}\n\n"
            f"相关知识:\n{review_context['knowledge_base_data']}\n\n"
            f"代码分析:\n{review_context['code_analysis_data']}"
        )

        return review_materials

    async def _analyze_potential_issues(self, analysis_result: str) -> List[str]:
        """分析潜在问题"""
        issues = []

        # 检查完整性
        if not self._check_completeness(analysis_result):
            issues.append("需求描述不完整")

        # 检查一致性
        if not self._check_consistency(analysis_result):
            issues.append("需求存在一致性问题")

        # 检查可测试性
        if not self._check_testability(analysis_result):
            issues.append("需求缺乏可测试性")

        # 检查可追溯性
        if not self._check_traceability(analysis_result):
            issues.append("需求缺乏可追溯性")

        return issues

    def _check_completeness(self, content: str) -> bool:
        """检查完整性"""
        required_sections = ["功能需求", "非功能需求", "业务规则", "接口定义"]

        return all(section in content for section in required_sections)

    def _check_consistency(self, content: str) -> bool:
        """检查一致性"""
        # TODO: 实现一致性检查逻辑
        return True

    def _check_testability(self, content: str) -> bool:
        """检查可测试性"""
        # TODO: 实现可测试性检查逻辑
        return True

    def _check_traceability(self, content: str) -> bool:
        """检查可追溯性"""
        # TODO: 实现可追溯性检查逻辑
        return True

    def _get_quality_metrics(self) -> Dict:
        """获取质量指标"""
        return {
            "completeness": 0.95,  # 完整性得分
            "consistency": 0.90,  # 一致性得分
            "testability": 0.85,  # 可测试性得分
            "traceability": 0.80,  # 可追溯性得分
            "overall": 0.875,  # 总体得分
        }
