"""
知识库独立模块

将知识库功能从特定助手中抽离，打造通用、可复用的知识管理模块：
- 支持多种知识类型（领域知识、技术模式、最佳实践等）
- 提供统一的知识检索和推荐接口
- 支持知识库的动态加载和更新
- 面向多个智能体提供知识服务
"""

from .service import KnowledgeService
from .types import KnowledgeEntry, KnowledgeType

__all__ = [
    "KnowledgeService",
    "KnowledgeType",
    "KnowledgeEntry",
]
