"""
工作流状态存储

提供工作流状态的存储和管理功能
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.logger import logger

from ..core.workflow_error import WorkflowError


class WorkflowStateData(BaseModel):
    """工作流状态数据模型"""

    workflow_id: str = Field(..., description="工作流ID")
    execution_id: str = Field(..., description="执行ID")
    status: str = Field(..., description="工作流状态")
    current_step: Optional[str] = Field(None, description="当前步骤")
    steps_completed: List[str] = Field(default_factory=list, description="已完成的步骤")
    steps_remaining: List[str] = Field(default_factory=list, description="剩余的步骤")
    progress: float = Field(default=0.0, description="进度")
    data: Dict = Field(default_factory=dict, description="工作流数据")
    error: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    metadata: Dict = Field(default_factory=dict, description="元数据")


class StateStore:
    """工作流状态存储"""

    def __init__(self):
        self._states = {}
        self._lock = asyncio.Lock()
        self._valid_statuses: Set[str] = {
            "pending",
            "running",
            "waiting_for_input",
            "completed",
            "failed",
            "terminated",
        }

    async def save_workflow_state(
        self, workflow_id: str, state: Dict[str, Any]
    ) -> None:
        """保存工作流状态"""
        async with self._lock:
            self._states[workflow_id] = state

    async def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        async with self._lock:
            return self._states.get(workflow_id)

    async def delete_workflow_state(self, workflow_id: str) -> None:
        """删除工作流状态"""
        async with self._lock:
            if workflow_id in self._states:
                del self._states[workflow_id]

    def _validate_status(self, status: str) -> None:
        """验证状态是否有效"""
        if status not in self._valid_statuses:
            raise WorkflowError(f"无效的工作流状态: {status}")

    async def update_workflow_progress(
        self, workflow_id: str, progress: float, current_step: Optional[str] = None
    ) -> None:
        """
        更新工作流进度

        Args:
            workflow_id: 工作流ID
            progress: 进度值 (0-1)
            current_step: 当前步骤名称
        """
        try:
            if not 0 <= progress <= 1:
                raise ValueError("进度值必须在0到1之间")

            async with self._lock:
                state = self._states.get(workflow_id)
                if not state:
                    raise WorkflowError(f"工作流 {workflow_id} 不存在")

                # 更新进度
                state["progress"] = progress
                if current_step:
                    state["current_step"] = current_step
                state["updated_at"] = datetime.now()

                # 记录进度更新
                logger.info(
                    f"工作流 {workflow_id} 进度更新: {progress:.1%}, "
                    f"当前步骤: {current_step or state['current_step']}"
                )

        except Exception as e:
            logger.error(f"更新工作流进度失败: {e}")
            raise WorkflowError(f"更新工作流进度失败: {str(e)}")

    async def mark_step_completed(
        self, workflow_id: str, step_name: str, step_data: Optional[Dict] = None
    ) -> None:
        """
        标记步骤为已完成

        Args:
            workflow_id: 工作流ID
            step_name: 步骤名称
            step_data: 步骤数据
        """
        try:
            async with self._lock:
                state = self._states.get(workflow_id)
                if not state:
                    raise WorkflowError(f"工作流 {workflow_id} 不存在")

                # 更新完成的步骤
                if step_name not in state["steps_completed"]:
                    state["steps_completed"].append(step_name)

                # 从剩余步骤中移除
                if step_name in state["steps_remaining"]:
                    state["steps_remaining"].remove(step_name)

                # 更新步骤数据
                if step_data:
                    state["data"][f"step_{step_name}"] = step_data

                state["updated_at"] = datetime.now()

                # 记录步骤完成
                logger.info(
                    f"工作流 {workflow_id} 步骤完成: {step_name}, "
                    f"已完成步骤: {len(state['steps_completed'])}, "
                    f"剩余步骤: {len(state['steps_remaining'])}"
                )

        except Exception as e:
            logger.error(f"标记步骤完成失败: {e}")
            raise WorkflowError(f"标记步骤完成失败: {str(e)}")

    async def clear_workflow_state(self, workflow_id: str) -> None:
        """
        清除工作流状态

        Args:
            workflow_id: 工作流ID
        """
        try:
            async with self._lock:
                if workflow_id in self._states:
                    del self._states[workflow_id]

                logger.info(f"已清除工作流 {workflow_id} 的状态")

        except Exception as e:
            logger.error(f"清除工作流状态失败: {e}")
            raise WorkflowError(f"清除工作流状态失败: {str(e)}")

    async def get_all_workflow_states(self) -> List[Dict]:
        """
        获取所有工作流状态

        Returns:
            List[Dict]: 所有工作流的状态数据
        """
        try:
            states = []
            for workflow_id in self._states:
                async with self._lock:
                    state = self._states[workflow_id]
                    if state:
                        states.append(state)
            return states

        except Exception as e:
            logger.error(f"获取所有工作流状态失败: {e}")
            raise WorkflowError(f"获取所有工作流状态失败: {str(e)}")

    async def cleanup_expired_states(self, max_age_hours: int = 24) -> None:
        """
        清理过期的工作流状态

        Args:
            max_age_hours: 最大保留时间（小时）
        """
        try:
            now = datetime.now()
            expired_workflows = []

            for workflow_id, state in self._states.items():
                age = now - state["created_at"]
                if age.total_seconds() > max_age_hours * 3600:
                    expired_workflows.append(workflow_id)

            for workflow_id in expired_workflows:
                await self.clear_workflow_state(workflow_id)

            if expired_workflows:
                logger.info(f"已清理 {len(expired_workflows)} 个过期的工作流状态")

        except Exception as e:
            logger.error(f"清理过期工作流状态失败: {e}")
            raise WorkflowError(f"清理过期工作流状态失败: {str(e)}")

    async def start_cleanup(self) -> None:
        """启动定期清理任务"""
        # TODO: 实现定期清理逻辑
        pass

    async def stop_cleanup(self) -> None:
        """停止定期清理任务"""
        # TODO: 实现停止清理逻辑
        pass
