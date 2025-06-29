"""
知识库独立模块 - Modules层

将知识库功能从特定助手中抽离，打造通用、可复用的知识管理模块：
- 支持多种知识类型（领域知识、技术模式、最佳实践等）
- 提供统一的知识检索和推荐接口
- 支持知识库的动态加载和更新
- 面向多个智能体提供知识服务

架构关系：
- 本模块属于Modules层，实现知识库管理的核心业务逻辑
- 被API层的app/api/knowledge_base.py调用，为接口提供功能支持
- 不直接处理HTTP请求，专注于业务逻辑实现

这种分层设计使得：
- 知识库功能可以被多个不同的接口复用
- 业务逻辑可以独立于接口进行测试和维护
- 底层实现变更不影响API接口
"""

from .service import KnowledgeService
from .types import KnowledgeEntry, KnowledgeType

__all__ = [
    "KnowledgeService",
    "KnowledgeType",
    "KnowledgeEntry",
]
