"""
项目管理事件发布者接口定义
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, List

from ..utils.events import ProjectEvent, RequirementEvent


class IEventPublisher(ABC):
    """事件发布者接口"""

    @abstractmethod
    async def publish_project_event(self, event: ProjectEvent) -> None:
        """发布项目事件"""
        pass

    @abstractmethod
    async def publish_requirement_event(self, event: RequirementEvent) -> None:
        """发布需求事件"""
        pass

    @abstractmethod
    def subscribe_project_event(self, handler: Callable[[ProjectEvent], Any]) -> None:
        """订阅项目事件"""
        pass

    @abstractmethod
    def subscribe_requirement_event(
        self, handler: Callable[[RequirementEvent], Any]
    ) -> None:
        """订阅需求事件"""
        pass

    @abstractmethod
    def unsubscribe_project_event(self, handler: Callable[[ProjectEvent], Any]) -> None:
        """取消订阅项目事件"""
        pass

    @abstractmethod
    def unsubscribe_requirement_event(
        self, handler: Callable[[RequirementEvent], Any]
    ) -> None:
        """取消订阅需求事件"""
        pass

    @abstractmethod
    def get_project_subscribers(self) -> List[Callable[[ProjectEvent], Any]]:
        """获取项目事件订阅者列表"""
        pass

    @abstractmethod
    def get_requirement_subscribers(self) -> List[Callable[[RequirementEvent], Any]]:
        """获取需求事件订阅者列表"""
        pass
