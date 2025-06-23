"""
代码库智能分析模块

提供代码库的智能分析和管理功能：
- 自动代码结构分析
- 智能相似度检测
- 代码复用建议
- 技术栈识别
- 工作量估算
- 代码质量评估
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
