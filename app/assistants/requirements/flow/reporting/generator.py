"""
需求分析流程的报告生成模块
"""

from datetime import datetime
from typing import Dict, List, Optional

from app.logger import logger

from ..core.base import BaseRequirementsFlow


class ReportGenerator:
    """报告生成器"""

    def __init__(self, flow: BaseRequirementsFlow):
        self.flow = flow

    async def _generate_final_report(self) -> str:
        """生成最终报告"""
        logger.info("开始生成最终报告")

        # 收集报告数据
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.flow.session_id,
            "project_id": self.flow.project_id,
            "original_input": self.flow.state_manager.get_data("user_input"),
            "clarification_result": self.flow.current_context.get(
                "clarification_result"
            ),
            "analysis_result": self.flow.current_context.get("analysis_result"),
            "documentation_result": self.flow.current_context.get(
                "documentation_result"
            ),
            "quality_metrics": self.flow._get_quality_metrics(),
            "knowledge_base_data": self.flow.knowledge_base.get_relevant_knowledge(),
            "code_analysis_data": self.flow.code_analyzer.get_analysis_results(),
        }

        # 生成报告
        report = self._format_report(report_data)

        return report

    def _format_report(self, data: Dict) -> str:
        """格式化报告"""
        report = f"""
# 需求分析报告

## 基本信息
- 生成时间：{data['timestamp']}
- 会话ID：{data['session_id']}
- 项目ID：{data['project_id']}

## 原始需求
{data['original_input']}

## 需求澄清结果
{data['clarification_result']}

## 业务分析结果
{data['analysis_result']}

## 需求规格说明
{data['documentation_result']}

## 质量评估
- 完整性：{data['quality_metrics']['completeness']}
- 一致性：{data['quality_metrics']['consistency']}
- 可测试性：{data['quality_metrics']['testability']}
- 可追溯性：{data['quality_metrics']['traceability']}
- 总体评分：{data['quality_metrics']['overall']}

## 相关知识
{data['knowledge_base_data']}

## 代码分析
{data['code_analysis_data']}
"""
        return report

    def _generate_progress_report(self) -> Dict:
        """生成进度报告"""
        return {
            "current_stage": self.flow._get_current_stage(),
            "clarification_complete": self.flow.clarification_complete,
            "analysis_complete": self.flow.analysis_complete,
            "state": self.flow.state_manager.current_state,
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_quality_report(self) -> Dict:
        """生成质量报告"""
        metrics = self.flow._get_quality_metrics()
        return {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_quality_recommendations(metrics),
        }

    def _generate_quality_recommendations(self, metrics: Dict) -> List[str]:
        """生成质量改进建议"""
        recommendations = []

        if metrics["completeness"] < 0.9:
            recommendations.append("建议补充完善需求描述的完整性")

        if metrics["consistency"] < 0.9:
            recommendations.append("建议检查并解决需求中的一致性问题")

        if metrics["testability"] < 0.9:
            recommendations.append("建议增加可测试的具体指标和验收标准")

        if metrics["traceability"] < 0.9:
            recommendations.append("建议加强需求项之间的关联性和可追溯性")

        return recommendations
