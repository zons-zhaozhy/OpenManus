"""
智能流程编排模块

替代硬编码的流程流转，实现更智能、更科学的流程管理：
- 基于规则的智能决策
- 动态流程路径规划
- 条件分支和并行处理
- 流程状态跟踪和回滚
- 自适应优化机制
"""

from .builder import WorkflowBuilder
from .core import WorkflowEngine
from .executor import WorkflowExecutor
from .monitor import WorkflowMonitor
from .types import (
    ExecutionResult,
    WorkflowCondition,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
    WorkflowState,
)

__all__ = [
    "WorkflowEngine",
    "WorkflowBuilder",
    "WorkflowExecutor",
    "WorkflowMonitor",
    "WorkflowDefinition",
    "WorkflowNode",
    "WorkflowEdge",
    "WorkflowCondition",
    "WorkflowState",
    "ExecutionResult",
]
