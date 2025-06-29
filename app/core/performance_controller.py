"""
性能控制器模块

负责系统性能监控、优化和控制
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from app.logger import logger


class PerformanceConfig(BaseModel):
    """性能配置"""

    # LLM相关配置
    llm_timeout_seconds: float = Field(default=30.0, description="LLM调用超时时间")
    llm_concurrent_limit: int = Field(default=5, description="LLM并发调用限制")
    llm_retry_limit: int = Field(default=3, description="LLM重试次数限制")

    # 熔断配置
    circuit_failure_threshold: int = Field(default=5, description="熔断失败阈值")
    circuit_recovery_time: float = Field(default=60.0, description="熔断恢复时间")

    # 性能阈值
    max_response_time: float = Field(default=10.0, description="最大响应时间")
    max_memory_usage: int = Field(
        default=1024 * 1024 * 1024, description="最大内存使用"
    )
    max_cpu_usage: float = Field(default=80.0, description="最大CPU使用率")
    max_concurrent_requests: int = Field(default=100, description="最大并发请求数")

    # 监控配置
    monitor_interval: float = Field(default=60.0, description="监控间隔时间")
    metrics_history_size: int = Field(default=1000, description="指标历史记录大小")


class PerformanceController:
    """性能控制器"""

    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()
        self.performance_metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "concurrent_requests": 0,
            "total_requests": 0,
            "errors": 0,
        }
        self.thresholds = {
            "max_response_time": self.config.max_response_time,
            "max_memory_usage": self.config.max_memory_usage,
            "max_cpu_usage": self.config.max_cpu_usage,
            "max_concurrent_requests": self.config.max_concurrent_requests,
        }
        self.start_time = time.time()
        self._monitor_task = None

    def timeout_control(self, timeout: Optional[float] = None):
        """
        超时控制装饰器

        Args:
            timeout: 超时时间（秒），如果为None则使用默认配置

        Returns:
            装饰器函数
        """
        timeout_seconds = timeout or self.config.llm_timeout_seconds

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    start_time = time.time()
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), timeout=timeout_seconds
                    )
                    if time.time() - start_time > timeout_seconds:
                        logger.warning(
                            f"函数 {func.__name__} 执行超时 ({timeout_seconds}s)"
                        )
                    return result
                except asyncio.TimeoutError:
                    logger.error(f"函数 {func.__name__} 执行超时 ({timeout_seconds}s)")
                    raise

            return wrapper

        return decorator

    def record_request_start(self):
        """记录请求开始"""
        self.performance_metrics["concurrent_requests"] += 1
        self.performance_metrics["total_requests"] += 1

    def record_request_end(self, response_time: float):
        """记录请求结束"""
        self.performance_metrics["concurrent_requests"] -= 1
        self.performance_metrics["response_times"].append(response_time)

        # 只保留最近N个响应时间
        if (
            len(self.performance_metrics["response_times"])
            > self.config.metrics_history_size
        ):
            self.performance_metrics["response_times"].pop(0)

    def record_error(self):
        """记录错误"""
        self.performance_metrics["errors"] += 1

    def get_average_response_time(self) -> float:
        """获取平均响应时间"""
        times = self.performance_metrics["response_times"]
        return sum(times) / len(times) if times else 0.0

    def get_error_rate(self) -> float:
        """获取错误率"""
        total = self.performance_metrics["total_requests"]
        return self.performance_metrics["errors"] / total * 100 if total > 0 else 0.0

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "uptime": time.time() - self.start_time,
            "avg_response_time": self.get_average_response_time(),
            "error_rate": self.get_error_rate(),
            "concurrent_requests": self.performance_metrics["concurrent_requests"],
            "total_requests": self.performance_metrics["total_requests"],
            "total_errors": self.performance_metrics["errors"],
        }

    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "stats": self.get_performance_stats(),
            "issues": self.check_performance_issues(),
            "config": self.config.dict(),
        }

    def check_performance_issues(self) -> List[str]:
        """检查性能问题"""
        issues = []

        # 检查响应时间
        avg_response_time = self.get_average_response_time()
        if avg_response_time > self.thresholds["max_response_time"]:
            issues.append(
                f"平均响应时间 ({avg_response_time:.2f}s) 超过阈值 ({self.thresholds['max_response_time']}s)"
            )

        # 检查并发请求
        if (
            self.performance_metrics["concurrent_requests"]
            > self.thresholds["max_concurrent_requests"]
        ):
            issues.append(
                f"并发请求数 ({self.performance_metrics['concurrent_requests']}) 超过阈值 ({self.thresholds['max_concurrent_requests']})"
            )

        # 检查错误率
        error_rate = self.get_error_rate()
        if error_rate > 5.0:  # 错误率超过5%
            issues.append(f"错误率 ({error_rate:.2f}%) 过高")

        return issues

    async def monitor_performance(self):
        """性能监控循环"""
        while True:
            try:
                issues = self.check_performance_issues()
                if issues:
                    logger.warning(f"发现性能问题: {', '.join(issues)}")

                stats = self.get_performance_stats()
                logger.info(f"性能统计: {stats}")

                await asyncio.sleep(self.config.monitor_interval)

            except Exception as e:
                logger.error(f"性能监控失败: {e}")
                await asyncio.sleep(self.config.monitor_interval)

    async def start_monitoring(self):
        """启动性能监控"""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self.monitor_performance())

    async def stop_monitoring(self):
        """停止性能监控"""
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def cleanup(self):
        """清理资源"""
        await self.stop_monitoring()


# 全局实例
performance_controller = PerformanceController()


async def init_performance_controller(
    config: Optional[PerformanceConfig] = None,
) -> PerformanceController:
    """初始化性能控制器"""
    global performance_controller
    performance_controller = PerformanceController(config)

    # 启动性能监控
    await performance_controller.start_monitoring()

    return performance_controller


def get_performance_controller() -> PerformanceController:
    """获取性能控制器实例"""
    global performance_controller
    return performance_controller
