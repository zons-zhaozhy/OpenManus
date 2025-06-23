"""
OpenManus核心架构模块

基于现有BaseAgent和BaseFlow架构的多智能体协作系统：
- 各助手继承BaseFlow，管理多个BaseAgent
- 充分利用现有的LLM、配置、提示词等基础设施
- 通过WorkflowEngine协调各助手间的协作
"""

from .coordination_hub import CoordinationHub
from .multi_agent_alliance import AgentRole, AssistantRole, MultiAgentAlliance, WorkItem
from .workflow_engine import WorkflowEngine

__all__ = [
    "MultiAgentAlliance",
    "WorkflowEngine",
    "CoordinationHub",
    "AssistantRole",
    "AgentRole",
    "WorkItem",
]
