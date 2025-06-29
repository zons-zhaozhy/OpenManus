"""
性能指标监控模块

提供性能指标收集和监控功能。
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.logger import get_logger

logger = get_logger(__name__)


class PerformanceMetrics:
    """性能指标监控器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceMetrics, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化性能指标"""
        self._metrics = {
            "quick_mode": {
                "total_requests": 0,
                "successful_requests": 0,
                "timeouts": 0,
                "response_times": [],
                "last_reset": datetime.now(),
            }
        }

    async def record_quick_analysis(self, duration: float, success: bool):
        """
        记录快速分析性能指标

        Args:
            duration: 处理时长（秒）
            success: 是否成功
        """
        metrics = self._metrics["quick_mode"]
        metrics["total_requests"] += 1
        metrics["response_times"].append(duration)

        if success:
            metrics["successful_requests"] += 1
        else:
            metrics["timeouts"] += 1

        # 只保留最近1000个响应时间样本
        if len(metrics["response_times"]) > 1000:
            metrics["response_times"] = metrics["response_times"][-1000:]

    def get_quick_mode_metrics(self) -> Dict:
        """
        获取快速模式性能指标

        Returns:
            Dict: 性能指标统计
        """
        metrics = self._metrics["quick_mode"]
        total = metrics["total_requests"]

        if total == 0:
            return {
                "success_rate": 0,
                "avg_response_time": 0,
                "p95_response_time": 0,
                "timeout_rate": 0,
                "total_requests": 0,
            }

        response_times = metrics["response_times"]

        return {
            "success_rate": metrics["successful_requests"] / total,
            "avg_response_time": (
                statistics.mean(response_times) if response_times else 0
            ),
            "p95_response_time": (
                statistics.quantiles(response_times, n=20)[18]
                if len(response_times) >= 20
                else max(response_times, default=0)
            ),
            "timeout_rate": metrics["timeouts"] / total,
            "total_requests": total,
        }

    async def reset_metrics(self):
        """重置所有性能指标"""
        self._initialize()


def get_performance_metrics() -> PerformanceMetrics:
    """
    获取性能指标监控器实例

    Returns:
        PerformanceMetrics: 性能指标监控器实例
    """
    return PerformanceMetrics()
