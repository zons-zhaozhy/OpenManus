"""
需求分析助手模块 - 重构版

基于OpenManus现有架构的多智能体需求分析系统：
- RequirementsFlow: 继承BaseFlow的流程管理
- 各种Agent: 继承BaseAgent的智能体实现
- 充分复用现有的LLM、配置等基础设施
"""

from .agents import (
    BusinessAnalystAgent,
    RequirementClarifierAgent,
    TechnicalWriterAgent,
)
from .flow import RequirementsFlow

__all__ = [
    "RequirementsFlow",
    "RequirementClarifierAgent",
    "BusinessAnalystAgent",
    "TechnicalWriterAgent",
]

# 向后兼容的别名（如果需要）
RequirementsAssistant = RequirementsFlow
