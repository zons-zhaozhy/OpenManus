"""
需求分析器接口定义
"""

from abc import ABC, abstractmethod
from typing import List

from ..models.base import Requirement
from ..services.requirement_analyzer import (
    RequirementAnalysis,
    Suggestion,
    ValidationResult,
)


class IRequirementAnalyzer(ABC):
    """需求分析器接口"""

    @abstractmethod
    async def analyze_requirement(self, text: str) -> RequirementAnalysis:
        """分析需求文本，提取关键信息"""
        pass

    @abstractmethod
    async def validate_requirement(self, requirement: Requirement) -> ValidationResult:
        """验证需求的完整性和一致性"""
        pass

    @abstractmethod
    async def suggest_improvements(self, requirement: Requirement) -> List[Suggestion]:
        """生成需求改进建议"""
        pass
