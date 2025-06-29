"""
基础智能体类

提供智能体的基本功能和接口定义
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from loguru import logger


class BaseAgent(ABC):
    """基础智能体类"""

    def __init__(self, name: str):
        self.name = name
        logger.info(f"初始化智能体: {name}")

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行智能体任务

        Args:
            inputs: 输入数据

        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()
