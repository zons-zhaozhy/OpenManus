"""
知识库基础模块
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.logger import logger


class KnowledgeBase(ABC):
    """知识库基类"""

    def __init__(self):
        self.cache: Dict[str, Any] = {}

    @abstractmethod
    async def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """查询知识库"""
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索知识"""
        pass

    @abstractmethod
    async def add(self, content: Dict[str, Any]) -> bool:
        """添加知识"""
        pass

    @abstractmethod
    async def update(self, id: str, content: Dict[str, Any]) -> bool:
        """更新知识"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除知识"""
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取知识"""
        pass

    def get_relevant_knowledge(self, context: str = "") -> List[Dict[str, Any]]:
        """获取相关知识"""
        if not context:
            return []
        return self.search(context)

    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        logger.info("知识库缓存已清除")
