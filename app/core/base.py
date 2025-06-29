"""
Base classes for OpenManus
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.core.agents import BaseAgent


class BaseFlow(ABC):
    """流程基类"""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        注册智能体

        Args:
            name: 智能体名称
            agent: 智能体实例
        """
        self._agents[name] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        获取智能体

        Args:
            name: 智能体名称

        Returns:
            Optional[BaseAgent]: 智能体实例
        """
        return self._agents.get(name)

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        执行流程

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 执行结果
        """
        pass
