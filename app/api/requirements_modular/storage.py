"""
会话存储模块

提供会话数据的存储和管理功能
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.logger import logger
from app.workflow.core.workflow_state import WorkflowState

from .exceptions import InvalidSessionError, SessionExpiredError, StorageError


class SessionStorage:
    """会话存储类"""

    def __init__(self, expiry_hours: int = 24):
        self._sessions: Dict[str, Dict] = {}
        self._expiry_hours = expiry_hours
        self._cleanup_task = None

    async def get(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        if not session_id:
            raise InvalidSessionError("Session ID cannot be empty")

        session = self._sessions.get(session_id)
        if not session:
            return None

        # Check expiry
        if self._is_expired(session):
            await self.delete(session_id)
            raise SessionExpiredError(f"Session {session_id} has expired")

        return session

    async def save(self, session_id: str, data: Dict) -> None:
        """保存会话"""
        if not session_id:
            raise InvalidSessionError("Session ID cannot be empty")

        try:
            # Ensure data is JSON serializable
            json.dumps(data)
            data["last_updated"] = datetime.now().isoformat()
            self._sessions[session_id] = data
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise StorageError(f"Failed to save session: {str(e)}")

    async def delete(self, session_id: str) -> None:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]

    async def list_all(self) -> List[Dict]:
        """列出所有会话"""
        return [s for s in self._sessions.values() if not self._is_expired(s)]

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        if not session_id:
            return False

        session = self._sessions.get(session_id)
        if not session:
            return False

        if self._is_expired(session):
            await self.delete(session_id)
            return False

        return True

    def _is_expired(self, session: Dict) -> bool:
        """检查会话是否过期"""
        last_updated = datetime.fromisoformat(
            session.get("last_updated", "2000-01-01T00:00:00")
        )
        return datetime.now() - last_updated > timedelta(hours=self._expiry_hours)

    async def start_cleanup(self) -> None:
        """启动清理任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        """停止清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """定期清理过期会话"""
        while True:
            try:
                expired_sessions = [
                    sid
                    for sid, session in self._sessions.items()
                    if self._is_expired(session)
                ]
                for sid in expired_sessions:
                    await self.delete(sid)
                await asyncio.sleep(3600)  # 每小时清理一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)


# 创建全局会话存储实例
session_storage = SessionStorage()


class WorkflowStorage:
    """工作流存储类"""

    def __init__(self, expiry_hours: int = 24):
        self._workflows: Dict[str, WorkflowState] = {}
        self._expiry_hours = expiry_hours
        self._cleanup_task = None

    async def get(self, workflow_id: str) -> Optional[WorkflowState]:
        """获取工作流状态"""
        if not workflow_id:
            raise InvalidSessionError("Workflow ID cannot be empty")

        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None

        # Check expiry
        if self._is_expired(workflow):
            await self.delete(workflow_id)
            raise SessionExpiredError(f"Workflow {workflow_id} has expired")

        return workflow

    async def save(self, state: WorkflowState) -> None:
        """保存工作流状态"""
        if not state or not state.id:
            raise InvalidSessionError("Invalid workflow state")

        try:
            # Update timestamps
            state.updated_at = datetime.now().isoformat()
            self._workflows[state.id] = state
        except Exception as e:
            logger.error(f"Failed to save workflow {state.id}: {e}")
            raise StorageError(f"Failed to save workflow: {str(e)}")

    async def delete(self, workflow_id: str) -> None:
        """删除工作流状态"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]

    async def list_all(self) -> List[WorkflowState]:
        """列出所有工作流状态"""
        return [w for w in self._workflows.values() if not self._is_expired(w)]

    async def exists(self, workflow_id: str) -> bool:
        """检查工作流是否存在"""
        if not workflow_id:
            return False

        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False

        if self._is_expired(workflow):
            await self.delete(workflow_id)
            return False

        return True

    def _is_expired(self, workflow: WorkflowState) -> bool:
        """检查工作流是否过期"""
        last_updated = datetime.fromisoformat(workflow.updated_at)
        return datetime.now() - last_updated > timedelta(hours=self._expiry_hours)

    async def start_cleanup(self) -> None:
        """启动清理任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        """停止清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """定期清理过期工作流"""
        while True:
            try:
                expired_workflows = [
                    wid
                    for wid, workflow in self._workflows.items()
                    if self._is_expired(workflow)
                ]
                for wid in expired_workflows:
                    await self.delete(wid)
                await asyncio.sleep(3600)  # 每小时清理一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)
