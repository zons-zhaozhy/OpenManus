"""
WebSocket事件发布者实现
"""

from typing import Any, Callable, List, Dict
import json
from fastapi import WebSocket

from ..interfaces.event_publisher import IEventPublisher
from ..utils.events import ProjectEvent, RequirementEvent


class WebSocketEventPublisher(IEventPublisher):
    """
    通过WebSocket发布事件的实现
    """

    def __init__(self, websocket_connections: Dict[str, WebSocket]):
        self.websocket_connections = websocket_connections
        self.project_subscribers: List[Callable[[ProjectEvent], Any]] = []
        self.requirement_subscribers: List[Callable[[RequirementEvent], Any]] = []

    async def publish_project_event(self, event: ProjectEvent) -> None:
        """
        发布项目事件
        """
        # 通知所有订阅者
        for subscriber in self.project_subscribers:
            await subscriber(event)

        # 通过WebSocket发送事件
        event_data = {
            "event_type": "project_event",
            "data": vars(event)
        }
        await self._broadcast_to_websocket(event_data)

    async def publish_requirement_event(self, event: RequirementEvent) -> None:
        """
        发布需求事件
        """
        # 通知所有订阅者
        for subscriber in self.requirement_subscribers:
            await subscriber(event)

        # 通过WebSocket发送事件
        event_data = {
            "event_type": "requirement_event",
            "data": vars(event)
        }
        await self._broadcast_to_websocket(event_data)

    async def publish_custom_event(self, session_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """
        发布自定义事件
        """
        event_data = {
            "event_type": event_type,
            "data": data
        }
        if session_id in self.websocket_connections:
            websocket = self.websocket_connections[session_id]
            await websocket.send_text(json.dumps(event_data))

    async def _broadcast_to_websocket(self, event_data: Dict[str, Any]) -> None:
        """
        向所有连接的WebSocket客户端广播事件
        """
        for session_id, websocket in self.websocket_connections.items():
            try:
                await websocket.send_text(json.dumps(event_data))
            except Exception as e:
                print(f"Error broadcasting to WebSocket {session_id}: {str(e)}")

    def subscribe_project_event(self, handler: Callable[[ProjectEvent], Any]) -> None:
        """
        订阅项目事件
        """
        self.project_subscribers.append(handler)

    def subscribe_requirement_event(self, handler: Callable[[RequirementEvent], Any]) -> None:
        """
        订阅需求事件
        """
        self.requirement_subscribers.append(handler)

    def unsubscribe_project_event(self, handler: Callable[[ProjectEvent], Any]) -> None:
        """
        取消订阅项目事件
        """
        if handler in self.project_subscribers:
            self.project_subscribers.remove(handler)

    def unsubscribe_requirement_event(self, handler: Callable[[RequirementEvent], Any]) -> None:
        """
        取消订阅需求事件
        """
        if handler in self.requirement_subscribers:
            self.requirement_subscribers.remove(handler)

    def get_project_subscribers(self) -> List[Callable[[ProjectEvent], Any]]:
        """
        获取项目事件订阅者列表
        """
        return self.project_subscribers

    def get_requirement_subscribers(self) -> List[Callable[[RequirementEvent], Any]]:
        """
        获取需求事件订阅者列表
        """
        return self.requirement_subscribers
