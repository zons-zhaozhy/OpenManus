"""
代码库智能分析模块 - Modules层

提供代码库的智能分析和管理功能：
- 自动代码结构分析
- 智能相似度检测
- 代码复用建议
- 技术栈识别
- 工作量估算
- 代码质量评估

架构关系：
- 本模块属于Modules层，实现代码库分析和管理的核心业务逻辑
- 被API层的app/api/codebase.py调用，为接口提供功能支持
- 不直接处理HTTP请求，专注于业务逻辑实现

这种分层设计使得：
- 代码库分析功能可以被多个不同的接口复用
- 业务逻辑可以独立于接口进行测试和维护
- 底层实现变更不影响API接口
"""

from .analyzer import CodeAnalyzer, SimilarityAnalyzer, StructureAnalyzer
from .core import CodebaseCore
from .manager import CodebaseManager
from .types import (
    AnalysisResult,
    CodebaseInfo,
    CodeComponent,
    SimilarityResult,
    TechStack,
)

__all__ = [
    "CodebaseCore",
    "CodeAnalyzer",
    "StructureAnalyzer",
    "SimilarityAnalyzer",
    "CodebaseManager",
    "CodebaseInfo",
    "AnalysisResult",
    "SimilarityResult",
    "TechStack",
    "CodeComponent",
]
