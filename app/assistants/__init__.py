"""
OpenManus助手模块

五大智能助手基于OpenManus现有架构：
- 需求分析助手：基于BaseFlow和BaseAgent实现
- 其他助手：框架已就绪，待完善实现
"""

from .requirements import RequirementsFlow

__all__ = [
    "RequirementsFlow",
    # 其他助手（框架已就绪）
    # "ArchitectureFlow",
    # "DevelopmentFlow",
    # "TestingFlow",
    # "DeploymentFlow",
]

# 向后兼容
RequirementsAssistant = RequirementsFlow
