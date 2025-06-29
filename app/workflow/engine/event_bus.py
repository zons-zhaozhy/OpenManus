"""
事件总线实现

提供工作流事件的发布和订阅功能
"""

import asyncio
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Union

from ..core.workflow_event import WorkflowEvent


class EventBus:
    """事件总线"""

    def __init__(self):
        self._subscribers: Dict[
            str, List[Callable[[Dict[str, Any]], Awaitable[None]]]
        ] = {}
        self._event_history: List[Dict] = []
        self._max_history_size = 1000

    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        发布事件

        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        # 记录事件
        event_record = {
            "type": event_type,
            "workflow_id": event_data.get("workflow_id"),
            "timestamp": datetime.now().isoformat(),
            "data": event_data,
        }
        self._event_history.append(event_record)

        # 维护历史大小
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size :]

        # 获取该事件类型的所有订阅者
        subscribers = self._subscribers.get(event_type, [])

        # 异步调用所有订阅者的处理函数
        await asyncio.gather(
            *[subscriber(event_data) for subscriber in subscribers],
            return_exceptions=True
        )

    async def subscribe(
        self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(
        self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    def get_event_history(
        self, event_type: str = None, workflow_id: str = None, limit: int = 100
    ) -> List[Dict]:
        """
        获取事件历史

        Args:
            event_type: 可选的事件类型过滤
            workflow_id: 可选的工作流ID过滤
            limit: 返回的最大事件数量

        Returns:
            List[Dict]: 过滤后的事件历史记录
        """
        filtered_history = self._event_history

        if event_type:
            filtered_history = [
                event for event in filtered_history if event["type"] == event_type
            ]

        if workflow_id:
            filtered_history = [
                event
                for event in filtered_history
                if event["workflow_id"] == workflow_id
            ]

        return filtered_history[-limit:]

    def clear_history(self) -> None:
        """清除事件历史"""
        self._event_history.clear()
