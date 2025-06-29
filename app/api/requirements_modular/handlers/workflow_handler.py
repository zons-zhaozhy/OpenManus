"""
需求分析工作流处理器

负责处理工作流相关的业务逻辑，协调各个智能体的工作
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from loguru import logger

from app.workflow.core.workflow_context import WorkflowContext
from app.workflow.core.workflow_state import WorkflowState
from app.workflow.engine.event_bus import EventBus
from app.workflow.engine.state_store import StateStore
from app.workflow.engine.workflow_engine import WorkflowEngine
from app.workflow.requirements.requirements_analysis_workflow import (
    RequirementsAnalysisWorkflow,
)

from ..models import WorkflowError, WorkflowStep
from ..storage import WorkflowStorage


class WorkflowHandler:
    """工作流处理器"""

    def __init__(self, storage: WorkflowStorage):
        """初始化工作流处理器"""
        self.storage = storage

        # 创建工作流引擎依赖
        self.state_store = StateStore()
        self.event_bus = EventBus()

        # 创建工作流引擎
        self.engine = WorkflowEngine(
            state_store=self.state_store,
            event_bus=self.event_bus,
            max_concurrent_workflows=10,
        )

    async def start_workflow(
        self,
        workflow_type: str,
        initial_requirements: str,
        project_context: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """启动新的需求分析工作流"""
        try:
            # 生成工作流ID
            workflow_id = str(uuid4())

            # 创建并注册工作流定义
            if workflow_type == "requirements_analysis":
                workflow = RequirementsAnalysisWorkflow(workflow_id)
                await self.engine.register_workflow(workflow)
            else:
                raise WorkflowError(f"不支持的工作流类型: {workflow_type}")

            # 创建工作流上下文
            context = WorkflowContext(
                workflow_id=workflow_id,
                execution_id=f"exec_{workflow_id}_{int(datetime.now().timestamp())}",
                status="pending",
                start_time=datetime.now(),
                data={
                    "workflow_type": workflow_type,
                    "initial_requirements": initial_requirements,
                    "project_context": project_context,
                    "user_id": user_id,
                },
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "created_by": user_id,
                },
            )

            # 初始化工作流状态
            initial_state = {
                "workflow_id": workflow_id,
                "status": "running",
                "current_step": "initial_analysis",
                "progress": 0,
                "steps_completed": [],
                "steps_remaining": [step.name for step in workflow.steps],
                "data": {
                    "initial_requirements": initial_requirements,
                    "project_context": project_context,
                    "user_answers": [],
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            await self.state_store.save_workflow_state(workflow_id, initial_state)

            # 执行工作流
            result = await self.engine.execute_workflow(
                workflow_id=workflow_id,
                input_data={
                    "initial_requirements": initial_requirements,
                    "project_context": project_context,
                    "user_answers": [],
                },
                context=context,
            )

            return workflow_id

        except Exception as e:
            logger.error(f"工作流启动失败: {e}")
            raise WorkflowError(f"工作流启动失败: {e}")

    async def get_workflow_status(
        self, workflow_id: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取工作流状态"""
        try:
            # 从状态存储中获取工作流状态
            state = await self.state_store.get_workflow_state(workflow_id)
            if not state:
                return {
                    "status": "not_found",
                    "message": f"未找到工作流 {workflow_id}",
                    "workflow_id": workflow_id,
                }

            return {
                "status": state.get("status", "unknown"),
                "current_step": state.get("current_step", ""),
                "progress": state.get("progress", 0),
                "message": state.get("message", ""),
                "workflow_id": workflow_id,
                "created_at": state.get("created_at", ""),
                "updated_at": state.get("updated_at", ""),
            }

        except Exception as e:
            logger.error(f"获取工作流状态失败: {e}")
            raise WorkflowError(f"获取工作流状态失败: {e}")

    async def get_progress(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流进度"""
        try:
            # 从状态存储中获取工作流状态
            state = await self.state_store.get_workflow_state(workflow_id)
            if not state:
                return None

            return {
                "status": state.get("status", "unknown"),
                "progress": state.get("progress", 0),
                "current_step": state.get("current_step"),
                "steps_completed": state.get("steps_completed", []),
                "steps_remaining": state.get("steps_remaining", []),
            }

        except Exception as e:
            logger.error(f"获取工作流进度失败: {e}")
            raise WorkflowError(f"获取工作流进度失败: {e}")

    async def execute_step(
        self,
        workflow_id: str,
        step_name: str,
        step_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行工作流步骤"""
        try:
            # 获取工作流状态
            state = await self.state_store.get_workflow_state(workflow_id)
            if not state:
                raise WorkflowError(f"工作流 {workflow_id} 不存在")

            # 执行步骤
            result = await self.engine.execute_step(
                workflow_id=workflow_id,
                step_name=step_name,
                step_data=step_data,
                context=state,
            )

            return result

        except Exception as e:
            logger.error(f"执行工作流步骤失败: {e}")
            raise WorkflowError(f"执行工作流步骤失败: {e}")

    async def terminate_workflow(
        self, workflow_id: str, user_id: Optional[str] = None
    ) -> None:
        """终止工作流"""
        try:
            # 获取工作流状态
            state = await self.state_store.get_workflow_state(workflow_id)
            if not state:
                raise WorkflowError(f"工作流 {workflow_id} 不存在")

            # 更新状态
            state["status"] = "terminated"
            state["end_time"] = datetime.now().isoformat()
            state["error"] = "工作流被用户终止"

            # 保存状态
            await self.state_store.save_workflow_state(workflow_id, state)

            # 发布终止事件
            await self.event_bus.publish(
                {
                    "type": "workflow_terminated",
                    "workflow_id": workflow_id,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"终止工作流失败: {e}")
            raise WorkflowError(f"终止工作流失败: {e}")
