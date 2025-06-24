"""
代码库分析类型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class TechStackType(Enum):
    """技术栈类型"""

    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"
    TESTING = "testing"
    MOBILE = "mobile"
    AI_ML = "ai_ml"
    OTHER = "other"


class ComponentType(Enum):
    """代码组件类型"""

    CLASS = "class"
    FUNCTION = "function"
    MODULE = "module"
    INTERFACE = "interface"
    ENUM = "enum"
    CONSTANT = "constant"
    VARIABLE = "variable"
    SERVICE = "service"
    CONTROLLER = "controller"
    MODEL = "model"
    UTIL = "util"


class CodeComplexity(Enum):
    """代码复杂度等级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class TechStack:
    """技术栈信息"""

    name: str
    version: Optional[str] = None
    type: TechStackType = TechStackType.OTHER
    confidence: float = 0.0
    description: str = ""
    used_files: List[str] = field(default_factory=list)


@dataclass
class CodeComponent:
    """代码组件"""

    name: str
    type: ComponentType
    file_path: str
    start_line: int
    end_line: int
    complexity: CodeComplexity = CodeComplexity.LOW
    dependencies: List[str] = field(default_factory=list)
    description: str = ""
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    annotations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimilarityResult:
    """相似度分析结果"""

    file1: str
    file2: str
    similarity_score: float
    similar_components: List[str] = field(default_factory=list)
    similarity_type: str = "structural"  # structural, semantic, functional
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeMetrics:
    """代码度量"""

    lines_of_code: int = 0
    lines_of_comments: int = 0
    cyclomatic_complexity: int = 0
    maintainability_index: float = 0.0
    code_duplication_ratio: float = 0.0
    test_coverage: float = 0.0
    technical_debt_ratio: float = 0.0


@dataclass
class QualityIssue:
    """代码质量问题"""

    type: str
    severity: str  # critical, major, minor, info
    file_path: str
    line_number: int
    message: str
    rule: str
    suggestion: str = ""


@dataclass
class AnalysisResult:
    """代码分析结果"""

    codebase_id: str
    analysis_time: datetime
    tech_stacks: List[TechStack] = field(default_factory=list)
    components: List[CodeComponent] = field(default_factory=list)
    similarities: List[SimilarityResult] = field(default_factory=list)
    metrics: CodeMetrics = field(default_factory=CodeMetrics)
    quality_issues: List[QualityIssue] = field(default_factory=list)
    file_count: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)  # language -> line count
    estimated_effort_days: float = 0.0
    reusability_score: float = 0.0
    suggestions: List[str] = field(default_factory=list)


@dataclass
class CodebaseInfo:
    """代码库基本信息"""

    id: str
    name: str
    description: str
    root_path: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    language_primary: Optional[str] = None
    size_mb: float = 0.0
    last_analysis: Optional[AnalysisResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeSearchQuery:
    """代码搜索查询"""

    query_text: str
    codebase_ids: List[str]
    component_types: List[ComponentType] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    max_results: int = 50
    include_content: bool = True


@dataclass
class CodeSearchResult:
    """代码搜索结果"""

    component: CodeComponent
    codebase_id: str
    relevance_score: float
    content_snippet: str = ""
    highlights: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkloadEstimation:
    """工作量估算"""

    total_days: float
    breakdown: Dict[str, float] = field(default_factory=dict)  # phase -> days
    confidence: float = 0.0
    assumptions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
