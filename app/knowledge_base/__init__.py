"""
知识库包
"""

from .adapters import EnhancedKnowledgeBaseAdapter
from .base import KnowledgeBase

# 为了向后兼容，将增强版适配器作为默认实现
VectorKnowledgeBase = EnhancedKnowledgeBaseAdapter

__all__ = ["KnowledgeBase", "VectorKnowledgeBase", "EnhancedKnowledgeBaseAdapter"]
