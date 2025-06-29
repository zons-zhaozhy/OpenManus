"""
代码分析的基础数据模型
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CodeComponent:
    """代码组件"""

    name: str
    type: str  # class, function, module, package
    file_path: str
    line_start: int
    line_end: int
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    complexity_score: int = 1  # 1-简单, 2-中等, 3-复杂
    reusability_score: float = 0.0  # 0.0-1.0
    associated_test_cases: List[str] = field(default_factory=list) # 关联的测试用例
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodePattern:
    """代码模式"""

    name: str
    pattern_type: str  # design_pattern, architectural_pattern, coding_pattern
    description: str
    files: List[str] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    related_requirements: List[str] = field(default_factory=list)


@dataclass
class TechnicalDebt:
    """技术债务"""

    file_path: str
    issue_type: str  # code_smell, complexity, duplication, security
    description: str
    severity: str  # low, medium, high, critical
    effort_to_fix: str  # small, medium, large
    impact_on_requirements: str = ""
