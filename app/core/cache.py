"""
缓存管理器 - 优化智能体协作性能

提供：
1. 智能体数据共享缓存
2. 分析结果缓存
3. 临时数据缓存
4. 性能监控
"""

import json
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta

from app.logger import get_logger

logger = get_logger(__name__)

class CacheManager:
    """缓存管理器类"""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._performance_metrics: Dict[str, Dict] = {}

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 3600,
        namespace: str = "default"
    ) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)
            namespace: 命名空间
        """
        try:
            start_time = time.time()

            # 构建缓存数据结构
            cache_data = {
                "value": value,
                "expire_at": datetime.now() + timedelta(seconds=expire),
                "namespace": namespace,
                "created_at": datetime.now().isoformat()
            }

            # 设置缓存
            self._cache[self._get_cache_key(key, namespace)] = cache_data

            # 记录性能指标
            duration = time.time() - start_time
            self._record_performance("set", duration, True)

            logger.debug(f"缓存设置成功: {key} (命名空间: {namespace})")

        except Exception as e:
            logger.error(f"缓存设置失败: {str(e)}")
            self._record_performance("set", time.time() - start_time, False)
            raise

    async def get(
        self,
        key: str,
        namespace: str = "default",
        default: Any = None
    ) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键
            namespace: 命名空间
            default: 默认值

        Returns:
            缓存值或默认值
        """
        try:
            start_time = time.time()

            # 获取缓存键
            cache_key = self._get_cache_key(key, namespace)

            # 检查缓存是否存在
            if cache_key not in self._cache:
                logger.debug(f"缓存未命中: {key} (命名空间: {namespace})")
                self._record_performance("get", time.time() - start_time, True, hit=False)
                return default

            # 获取缓存数据
            cache_data = self._cache[cache_key]

            # 检查是否过期
            if datetime.now() > cache_data["expire_at"]:
                logger.debug(f"缓存已过期: {key} (命名空间: {namespace})")
                del self._cache[cache_key]
                self._record_performance("get", time.time() - start_time, True, hit=False)
                return default

            # 记录性能指标
            duration = time.time() - start_time
            self._record_performance("get", duration, True, hit=True)

            logger.debug(f"缓存命中: {key} (命名空间: {namespace})")
            return cache_data["value"]

        except Exception as e:
            logger.error(f"缓存获取失败: {str(e)}")
            self._record_performance("get", time.time() - start_time, False)
            return default

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        删除缓存

        Args:
            key: 缓存键
            namespace: 命名空间

        Returns:
            bool: 是否删除成功
        """
        try:
            start_time = time.time()

            cache_key = self._get_cache_key(key, namespace)
            if cache_key in self._cache:
                del self._cache[cache_key]
                self._record_performance("delete", time.time() - start_time, True)
                logger.debug(f"缓存删除成功: {key} (命名空间: {namespace})")
                return True

            self._record_performance("delete", time.time() - start_time, True)
            return False

        except Exception as e:
            logger.error(f"缓存删除失败: {str(e)}")
            self._record_performance("delete", time.time() - start_time, False)
            return False

    async def clear(self, namespace: Optional[str] = None) -> None:
        """
        清除缓存

        Args:
            namespace: 可选的命名空间，如果指定则只清除该命名空间下的缓存
        """
        try:
            start_time = time.time()

            if namespace:
                # 清除指定命名空间的缓存
                keys_to_delete = [
                    k for k, v in self._cache.items()
                    if v["namespace"] == namespace
                ]
                for key in keys_to_delete:
                    del self._cache[key]
                logger.info(f"已清除命名空间 {namespace} 下的所有缓存")
            else:
                # 清除所有缓存
                self._cache.clear()
                logger.info("已清除所有缓存")

            self._record_performance("clear", time.time() - start_time, True)

        except Exception as e:
            logger.error(f"缓存清除失败: {str(e)}")
            self._record_performance("clear", time.time() - start_time, False)
            raise

    def _get_cache_key(self, key: str, namespace: str) -> str:
        """生成缓存键"""
        return f"{namespace}:{key}"

    def _record_performance(
        self,
        operation: str,
        duration: float,
        success: bool,
        hit: bool = None
    ) -> None:
        """记录性能指标"""
        if operation not in self._performance_metrics:
            self._performance_metrics[operation] = {
                "total_count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_duration": 0,
                "hit_count": 0 if operation == "get" else None,
                "miss_count": 0 if operation == "get" else None
            }

        metrics = self._performance_metrics[operation]
        metrics["total_count"] += 1
        metrics["success_count"] += 1 if success else 0
        metrics["error_count"] += 0 if success else 1
        metrics["total_duration"] += duration

        if operation == "get" and hit is not None:
            metrics["hit_count"] += 1 if hit else 0
            metrics["miss_count"] += 0 if hit else 1

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        metrics = {}
        for operation, data in self._performance_metrics.items():
            metrics[operation] = {
                "avg_duration": data["total_duration"] / data["total_count"] if data["total_count"] > 0 else 0,
                "success_rate": data["success_count"] / data["total_count"] * 100 if data["total_count"] > 0 else 0,
                "hit_rate": data["hit_count"] / data["total_count"] * 100 if operation == "get" and data["total_count"] > 0 else None,
                **data
            }
        return metrics

# 全局缓存管理器实例
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
