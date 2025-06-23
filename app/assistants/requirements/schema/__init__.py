"""
需求分析数据模型

定义需求分析过程中使用的所有数据结构和模型。
"""

from .requirement_models import (
    ClarificationQuestion,
    FunctionalRequirement,
    NonFunctionalRequirement,
    RequirementContext,
    RequirementItem,
    Stakeholder,
)
from .specification_models import (
    RequirementMatrix,
    RequirementSpecification,
    SpecificationSection,
)

__all__ = [
    "RequirementContext",
    "ClarificationQuestion",
    "RequirementItem",
    "FunctionalRequirement",
    "NonFunctionalRequirement",
    "Stakeholder",
    "RequirementSpecification",
    "SpecificationSection",
    "RequirementMatrix",
]
