"""
需求数据模型

定义需求分析过程中的核心数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RequirementType(Enum):
    """需求类型枚举"""

    FUNCTIONAL = "功能性需求"
    NON_FUNCTIONAL = "非功能性需求"
    CONSTRAINT = "约束条件"
    ASSUMPTION = "假设条件"


class RequirementPriority(Enum):
    """需求优先级枚举"""

    CRITICAL = "关键"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class Stakeholder:
    """利益相关者"""

    id: str
    name: str
    role: str
    department: Optional[str] = None
    contact: Optional[str] = None


@dataclass
class RequirementContext:
    """需求上下文"""

    domain: str  # 业务领域
    stakeholders: List[Stakeholder] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class ClarificationQuestion:
    """澄清问题"""

    id: str
    text: str
    category: str  # 问题分类
    priority: str  # 问题优先级


@dataclass
class RequirementItem:
    """需求项基类"""

    id: str
    title: str
    description: str
    requirement_type: RequirementType
    priority: RequirementPriority


@dataclass
class FunctionalRequirement(RequirementItem):
    """功能性需求"""

    user_story: str = ""
    use_cases: List[str] = field(default_factory=list)


@dataclass
class NonFunctionalRequirement(RequirementItem):
    """非功能性需求"""

    category: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
