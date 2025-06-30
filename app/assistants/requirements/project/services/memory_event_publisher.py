"""
基于内存的事件发布者实现
"""

from typing import Any, Callable, List

from ..interfaces.event_publisher import IEventPublisher
from ..utils.events import ProjectEvent, RequirementEvent


class MemoryEventPublisher(IEventPublisher):
    """基于内存的事件发布者实现"""

    def __init__(self):
        self._project_subscribers: List[Callable[[ProjectEvent], Any]] = []
        self._requirement_subscribers: List[Callable[[RequirementEvent], Any]] = []

    async def publish_project_event(self, event: ProjectEvent) -> None:
        """发布项目事件"""
        for subscriber in self._project_subscribers:
            try:
                await subscriber(event)
            except Exception as e:
                # TODO: 添加日志记录
                print(f"Error publishing project event to subscriber: {e}")

    async def publish_requirement_event(self, event: RequirementEvent) -> None:
        """发布需求事件"""
        for subscriber in self._requirement_subscribers:
            try:
                await subscriber(event)
            except Exception as e:
                # TODO: 添加日志记录
                print(f"Error publishing requirement event to subscriber: {e}")

    def subscribe_project_event(self, handler: Callable[[ProjectEvent], Any]) -> None:
        """订阅项目事件"""
        if handler not in self._project_subscribers:
            self._project_subscribers.append(handler)

    def subscribe_requirement_event(
        self, handler: Callable[[RequirementEvent], Any]
    ) -> None:
        """订阅需求事件"""
        if handler not in self._requirement_subscribers:
            self._requirement_subscribers.append(handler)

    def unsubscribe_project_event(self, handler: Callable[[ProjectEvent], Any]) -> None:
        """取消订阅项目事件"""
        if handler in self._project_subscribers:
            self._project_subscribers.remove(handler)

    def unsubscribe_requirement_event(
        self, handler: Callable[[RequirementEvent], Any]
    ) -> None:
        """取消订阅需求事件"""
        if handler in self._requirement_subscribers:
            self._requirement_subscribers.remove(handler)

    def get_project_subscribers(self) -> List[Callable[[ProjectEvent], Any]]:
        """获取项目事件订阅者列表"""
        return self._project_subscribers.copy()

    def get_requirement_subscribers(self) -> List[Callable[[RequirementEvent], Any]]:
        """获取需求事件订阅者列表"""
        return self._requirement_subscribers.copy()
