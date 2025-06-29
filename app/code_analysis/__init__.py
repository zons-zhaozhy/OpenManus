"""
代码分析包
"""

from .adapters import EnhancedCodeAnalyzerAdapter
from .models.base import CodeComponent, CodePattern, TechnicalDebt

# 为了向后兼容，将增强版适配器作为默认实现
CodeAnalyzer = EnhancedCodeAnalyzerAdapter

__all__ = [
    "CodeAnalyzer",
    "CodeComponent",
    "CodePattern",
    "TechnicalDebt",
    "EnhancedCodeAnalyzerAdapter",
]
