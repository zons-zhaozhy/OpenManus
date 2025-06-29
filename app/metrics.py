"""
性能指标收集器

负责收集和管理系统性能指标，包括：
- 时间指标
- 计数指标
- 事件记录
- 统计分析
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """性能指标收集器"""

    def __init__(self):
        """初始化指标收集器"""
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._events: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._agent_metrics: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    def initialize_metrics(self, metric_names: List[str]) -> None:
        """
        初始化指标列表

        Args:
            metric_names: 指标名称列表
        """
        for name in metric_names:
            if name not in self._metrics:
                self._metrics[name] = []
                logger.debug(f"初始化指标: {name}")

    def register_agent(self, agent_id: str) -> None:
        """
        注册智能体的指标收集

        Args:
            agent_id: 智能体ID
        """
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = {}
            logger.debug(f"注册智能体指标收集: {agent_id}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        同步获取所有指标数据

        Returns:
            Dict[str, Any]: 指标数据
        """
        result = {}
        for name in self._metrics:
            result[name] = {
                "count": len(self._metrics[name]),
                "latest": (
                    self._metrics[name][-1]["value"] if self._metrics[name] else None
                ),
            }
        return result

    async def record_metric(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录性能指标

        Args:
            name: 指标名称
            value: 指标值
            labels: 标签
        """
        async with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []

            metric = {
                "timestamp": datetime.now().isoformat(),
                "value": value,
                "labels": labels or {},
            }
            self._metrics[name].append(metric)

            # 记录异常值
            if await self._is_anomaly(name, value):
                logger.warning(f"检测到异常指标: {name}={value}, labels={labels}")

    def record_event_sync(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        同步记录事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }
        self._events.append(event)

    async def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        记录事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        async with self._lock:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "data": data,
            }
            self._events.append(event)

    async def _calculate_stats(self, values: List[float]) -> Tuple[float, float]:
        """
        计算均值和标准差

        Args:
            values: 数值列表

        Returns:
            Tuple[float, float]: (均值, 标准差)
        """
        if not values:
            return 0.0, 0.0

        mean = sum(values) / len(values)
        squared_diff_sum = sum((x - mean) ** 2 for x in values)
        std = (squared_diff_sum / len(values)) ** 0.5
        return mean, std

    async def _is_anomaly(self, metric_name: str, value: float) -> bool:
        """
        检测指标是否异常

        使用改进的异常检测算法：
        1. 使用最近的历史数据计算基线
        2. 计算Z分数
        3. 使用动态阈值进行判断

        Args:
            metric_name: 指标名称
            value: 指标值

        Returns:
            bool: 是否异常
        """
        if metric_name not in self._metrics or len(self._metrics[metric_name]) < 10:
            return False

        # 获取最近的历史数据
        recent_values = [m["value"] for m in self._metrics[metric_name][-10:]]
        mean, std = await self._calculate_stats(recent_values)

        # 如果标准差接近0，说明数据几乎不变
        if std < 1e-10:
            # 如果新值与均值的差异超过一定阈值，认为是异常
            return abs(value - mean) > 1.0

        # 计算Z分数
        z_score = abs(value - mean) / std

        # 使用动态阈值
        # 根据数据的分布特征调整阈值
        threshold = 2.0  # 默认使用2个标准差
        if len(recent_values) >= 30:
            # 如果有足够多的数据，可以使用更严格的阈值
            threshold = 1.5

        is_anomaly = z_score > threshold

        if is_anomaly:
            logger.debug(
                f"异常指标详情: name={metric_name}, value={value}, "
                f"mean={mean:.2f}, std={std:.2f}, z_score={z_score:.2f}, "
                f"threshold={threshold:.2f}"
            )

        return is_anomaly

    async def get_metric_statistics(
        self, name: str, start_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        获取指标统计信息

        Args:
            name: 指标名称
            start_time: 开始时间

        Returns:
            Dict[str, float]: 统计信息
        """
        if name not in self._metrics:
            return {}

        metrics = self._metrics[name]
        if start_time:
            metrics = [
                m
                for m in metrics
                if datetime.fromisoformat(m["timestamp"]) >= start_time
            ]

        if not metrics:
            return {}

        values = [m["value"] for m in metrics]
        sorted_values = sorted(values)
        mean, std = await self._calculate_stats(values)

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": mean,
            "std": std,
            "p50": sorted_values[int(len(values) * 0.5)],
            "p90": sorted_values[int(len(values) * 0.9)],
            "p95": sorted_values[int(len(values) * 0.95)],
            "p99": sorted_values[int(len(values) * 0.99)],
        }

    async def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有指标数据

        Returns:
            Dict[str, Dict[str, Any]]: 指标数据
        """
        result = {}
        for name in self._metrics:
            result[name] = await self.get_metric_statistics(name)
        result["events"] = self._events
        return result

    async def clear_old_metrics(self, before: datetime) -> None:
        """
        清除旧的指标数据

        Args:
            before: 清除该时间之前的数据
        """
        async with self._lock:
            for name in self._metrics:
                self._metrics[name] = [
                    m
                    for m in self._metrics[name]
                    if datetime.fromisoformat(m["timestamp"]) >= before
                ]

            self._events = [
                e
                for e in self._events
                if datetime.fromisoformat(e["timestamp"]) >= before
            ]

    def get_metric_labels(self, name: str) -> List[str]:
        """
        获取指标的所有标签

        Args:
            name: 指标名称

        Returns:
            List[str]: 标签列表
        """
        if name not in self._metrics:
            return []

        labels = set()
        for metric in self._metrics[name]:
            labels.update(metric.get("labels", {}).keys())
        return sorted(list(labels))

    async def get_metrics_by_label(
        self, name: str, label: str, value: str
    ) -> List[Dict[str, Any]]:
        """
        获取指定标签的指标数据

        Args:
            name: 指标名称
            label: 标签名
            value: 标签值

        Returns:
            List[Dict[str, Any]]: 指标数据列表
        """
        if name not in self._metrics:
            return []

        return [
            m for m in self._metrics[name] if m.get("labels", {}).get(label) == value
        ]
