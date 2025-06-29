"""
向量存储类型定义
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VectorSearchQuery:
    """向量搜索查询"""

    query_text: str
    knowledge_base_ids: List[str]
    top_k: int = 10
    min_score: float = 0.0
    filters: Optional[Dict[str, Any]] = None


@dataclass
class VectorSearchResult:
    """向量搜索结果"""

    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    knowledge_base_id: str
