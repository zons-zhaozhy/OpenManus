"""
需求澄清核心模块

模块化重构：
- quality_assessor: 质量评估功能
- question_generator: 问题生成功能
- conflict_analyzer: 冲突分析功能
- report_generator: 报告生成功能
"""

from .quality_assessor import DimensionQuality, QualityAssessor, RequirementDimension
from .question_generator import (
    ClarificationGoal,
    ImpactScope,
    MissingAspectClassification,
    MissingAspectPriority,
    QuestionGenerator,
    RiskLevel,
)

__all__ = [
    "QualityAssessor",
    "RequirementDimension",
    "DimensionQuality",
    "QuestionGenerator",
    "ClarificationGoal",
    "MissingAspectClassification",
    "MissingAspectPriority",
    "ImpactScope",
    "RiskLevel",
]
