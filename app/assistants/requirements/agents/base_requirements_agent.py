"""
基础需求分析智能体

提供需求分析的基础功能和共享特性
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.cache import get_cache_manager
from app.logger import get_logger

logger = get_logger(__name__)


class BaseRequirementsAgent(ABC):
    """需求分析智能体基类"""

    def __init__(self, flow_manager):
        """初始化基础需求分析智能体

        Args:
            flow_manager: 工作流管理器
        """
        self.flow_manager = flow_manager
        self.agent_name = "base_requirements_agent"
        self.cache = get_cache_manager()
        logger.debug(f"基础需求分析智能体初始化完成")

    @abstractmethod
    async def clarify_requirements(
        self, requirement: str, knowledge: Dict[str, Any], code_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """澄清需求，提出问题并整理需求

        Args:
            requirement: 原始需求文本
            knowledge: 相关知识库内容
            code_analysis: 相关代码分析结果

        Returns:
            Dict[str, Any]: 澄清结果
        """
        pass

    def get_name(self) -> str:
        """获取智能体名称

        Returns:
            str: 智能体名称
        """
        return self.agent_name

    def set_name(self, name: str) -> None:
        """设置智能体名称

        Args:
            name: 智能体名称
        """
        self.agent_name = name

    async def _get_cached_analysis(self, requirement_text: str) -> Optional[Dict]:
        """获取缓存的分析结果"""
        cache_key = f"analysis:{self.agent_name}:{hash(requirement_text)}"
        return await self.cache.get(cache_key, namespace="requirements")

    async def _cache_analysis(self, requirement_text: str, result: Dict) -> None:
        """缓存分析结果"""
        cache_key = f"analysis:{self.agent_name}:{hash(requirement_text)}"
        await self.cache.set(
            cache_key, result, expire=3600, namespace="requirements"  # 1小时过期
        )

    async def _get_shared_context(self) -> Dict[str, Any]:
        """获取共享上下文"""
        return await self.cache.get("shared_context", namespace="requirements") or {}

    async def _update_shared_context(self, context: Dict[str, Any]) -> None:
        """更新共享上下文"""
        current = await self._get_shared_context()
        current.update(context)
        await self.cache.set(
            "shared_context",
            current,
            expire=7200,  # 2小时过期
            namespace="requirements",
        )

    async def analyze(self, requirement_text: str, **kwargs) -> Dict:
        """
        分析需求

        Args:
            requirement_text: 需求文本
            **kwargs: 额外参数

        Returns:
            Dict: 分析结果
        """
        try:
            # 检查缓存
            cached_result = await self._get_cached_analysis(requirement_text)
            if cached_result:
                logger.info(f"使用缓存的分析结果: {self.agent_name}")
                return cached_result

            # 获取共享上下文
            shared_context = await self._get_shared_context()

            # 执行实际分析
            result = await self._analyze(
                requirement_text, shared_context=shared_context, **kwargs
            )

            # 缓存结果
            await self._cache_analysis(requirement_text, result)

            # 更新共享上下文
            await self._update_shared_context(
                {
                    "last_analysis": {
                        "agent_name": self.agent_name,
                        "timestamp": datetime.now().isoformat(),
                        "requirement_text": requirement_text,
                        "result_summary": result.get("summary", ""),
                    }
                }
            )

            return result

        except Exception as e:
            logger.error(f"需求分析失败: {str(e)}")
            raise

    async def _analyze(
        self, requirement_text: str, shared_context: Dict[str, Any], **kwargs
    ) -> Dict:
        """
        实际的分析实现

        子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现_analyze方法")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return await self.cache.get_performance_metrics()
