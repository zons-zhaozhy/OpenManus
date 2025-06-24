"""
知识库核心数据类型定义
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class KnowledgeType(str, Enum):
    """知识类型枚举"""

    DOMAIN_KNOWLEDGE = "domain_knowledge"  # 领域知识
    TECHNICAL_PATTERNS = "technical_patterns"  # 技术模式
    BEST_PRACTICES = "best_practices"  # 最佳实践
    REQUIREMENTS_TEMPLATES = "requirements_templates"  # 需求模板
    ARCHITECTURE_PATTERNS = "architecture_patterns"  # 架构模式
    BUSINESS_RULES = "business_rules"  # 业务规则
    QUALITY_STANDARDS = "quality_standards"  # 质量标准
    PROCESS_TEMPLATES = "process_templates"  # 流程模板


class KnowledgeScope(str, Enum):
    """知识适用范围"""

    GLOBAL = "global"  # 全局通用
    PROJECT = "project"  # 项目特定
    DOMAIN = "domain"  # 领域特定
    TEAM = "team"  # 团队特定


class KnowledgeEntry(BaseModel):
    """知识条目"""

    id: str = Field(..., description="知识条目唯一标识")
    title: str = Field(..., description="知识标题")
    content: str = Field(..., description="知识内容")
    summary: str = Field(..., description="知识摘要")

    # 分类信息
    type: KnowledgeType = Field(..., description="知识类型")
    scope: KnowledgeScope = Field(default=KnowledgeScope.GLOBAL, description="适用范围")
    category: str = Field(..., description="知识分类")
    tags: List[str] = Field(default_factory=list, description="知识标签")

    # 关联信息
    related_domains: List[str] = Field(default_factory=list, description="相关领域")
    prerequisites: List[str] = Field(default_factory=list, description="前置条件")
    applications: List[str] = Field(default_factory=list, description="应用场景")

    # 质量信息
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="可信度")
    usage_count: int = Field(default=0, description="使用次数")
    effectiveness_score: float = Field(default=0.0, description="有效性评分")

    # 元数据
    source: str = Field(..., description="知识来源")
    author: Optional[str] = Field(None, description="知识作者")
    version: str = Field(default="1.0.0", description="版本号")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 扩展属性
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class KnowledgePattern(BaseModel):
    """知识模式 - 用于模式识别和推荐"""

    id: str = Field(..., description="模式唯一标识")
    name: str = Field(..., description="模式名称")
    description: str = Field(..., description="模式描述")

    # 模式特征
    keywords: List[str] = Field(..., description="关键词列表")
    context_indicators: List[str] = Field(
        default_factory=list, description="上下文指示器"
    )
    trigger_conditions: List[str] = Field(default_factory=list, description="触发条件")

    # 关联知识
    related_knowledge: List[str] = Field(
        default_factory=list, description="相关知识ID列表"
    )
    recommended_actions: List[str] = Field(default_factory=list, description="推荐行动")

    # 模式质量
    accuracy: float = Field(default=0.8, ge=0.0, le=1.0, description="识别准确率")
    relevance: float = Field(default=0.8, ge=0.0, le=1.0, description="相关性")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class KnowledgeQuery(BaseModel):
    """知识查询请求"""

    query_text: str = Field(..., description="查询文本")
    knowledge_base_ids: Optional[List[str]] = Field(
        None, description="指定知识库ID列表"
    )
    knowledge_types: Optional[List[KnowledgeType]] = Field(
        None, description="指定知识类型"
    )
    domains: Optional[List[str]] = Field(None, description="指定领域")
    categories: Optional[List[str]] = Field(None, description="指定分类")
    tags: Optional[List[str]] = Field(None, description="指定标签")

    # 查询参数
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="最小可信度")
    include_patterns: bool = Field(default=True, description="是否包含模式匹配")

    # 上下文信息
    context: Dict[str, Any] = Field(default_factory=dict, description="查询上下文")


class KnowledgeSearchResult(BaseModel):
    """知识搜索结果"""

    entry: KnowledgeEntry = Field(..., description="知识条目")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="相关性评分")
    match_type: str = Field(..., description="匹配类型")
    matched_keywords: List[str] = Field(
        default_factory=list, description="匹配的关键词"
    )
    explanation: str = Field(..., description="推荐解释")


class KnowledgeSearchResponse(BaseModel):
    """知识搜索响应（简化版本）"""

    query: str = Field(..., description="查询文本")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="搜索结果")
    total_results: int = Field(default=0, description="总结果数")
    search_time_ms: float = Field(default=0.0, description="搜索时间（毫秒）")


class KnowledgeRecommendation(BaseModel):
    """知识推荐"""

    query: str = Field(..., description="原始查询")
    results: List[KnowledgeSearchResult] = Field(..., description="搜索结果")
    patterns: List[KnowledgePattern] = Field(
        default_factory=list, description="识别的模式"
    )
    suggestions: List[str] = Field(default_factory=list, description="改进建议")

    # 推荐质量
    total_results: int = Field(..., description="总结果数")
    avg_relevance: float = Field(default=0.0, description="平均相关性")
    processing_time: float = Field(default=0.0, description="处理时间（秒）")

    # 元数据
    timestamp: datetime = Field(default_factory=datetime.now)


class KnowledgeBase(BaseModel):
    """知识库配置"""

    id: str = Field(..., description="知识库唯一标识")
    name: str = Field(..., description="知识库名称")
    description: str = Field(..., description="知识库描述")

    # 配置信息
    type: KnowledgeType = Field(..., description="主要知识类型")
    scope: KnowledgeScope = Field(default=KnowledgeScope.GLOBAL, description="适用范围")

    # 存储配置
    storage_type: str = Field(default="file", description="存储类型")
    storage_path: str = Field(..., description="存储路径")
    index_config: Dict[str, Any] = Field(default_factory=dict, description="索引配置")

    # 访问控制
    is_public: bool = Field(default=True, description="是否公开")
    allowed_agents: List[str] = Field(
        default_factory=list, description="允许访问的智能体"
    )

    # 质量控制
    auto_update: bool = Field(default=False, description="是否自动更新")
    quality_threshold: float = Field(default=0.7, description="质量阈值")

    # 统计信息
    total_entries: int = Field(default=0, description="总条目数")
    last_updated: datetime = Field(default_factory=datetime.now)

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
