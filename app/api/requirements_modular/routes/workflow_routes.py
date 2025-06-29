"""
需求分析工作流路由

处理与需求分析工作流相关的所有HTTP请求
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.logger import logger

from ..handlers.workflow_handler import WorkflowHandler
from ..middleware.auth import get_current_user
from ..models import WorkflowError, WorkflowResponse, WorkflowState, WorkflowStep
from ..storage import WorkflowStorage
from ..utils.response import create_response


class WorkflowStartRequest(BaseModel):
    """工作流启动请求"""

    workflow_type: str = Field(..., description="工作流类型")
    requirement_text: str = Field(..., description="需求文本")
    project_context: Optional[str] = Field(None, description="项目上下文")


class WorkflowStepRequest(BaseModel):
    """工作流步骤请求"""

    step_name: str = Field(..., description="步骤名称")
    step_data: Dict[str, Any] = Field(default_factory=dict, description="步骤数据")


# 创建工作流路由器 - 添加/workflow前缀
router = APIRouter(prefix="/workflow", tags=["workflow"])


# 全局工作流存储实例
workflow_storage = WorkflowStorage()


def get_workflow_handler() -> WorkflowHandler:
    """获取工作流处理器"""
    return WorkflowHandler(workflow_storage)


@router.on_event("startup")
async def startup_event():
    """启动事件处理"""
    await workflow_storage.start_cleanup()


@router.on_event("shutdown")
async def shutdown_event():
    """关闭事件处理"""
    await workflow_storage.stop_cleanup()


@router.post("/start", response_model=WorkflowResponse)
async def start_workflow(
    request: WorkflowStartRequest,
    handler: WorkflowHandler = Depends(get_workflow_handler),
    user: Optional[str] = Depends(get_current_user),
) -> WorkflowResponse:
    """启动新的需求分析工作流"""
    try:
        workflow_id = await handler.start_workflow(
            workflow_type=request.workflow_type,
            initial_requirements=request.requirement_text,
            project_context=request.project_context,
            user_id=user,
        )

        return WorkflowResponse(
            status="success",
            message="工作流启动成功",
            workflow_id=workflow_id,
            data={"workflow_id": workflow_id},
            timestamp=datetime.now(),
        )

    except WorkflowError as e:
        logger.error(f"工作流启动失败: {e}")
        return WorkflowResponse(
            status="error",
            message=str(e),
            error=str(e),
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"工作流启动失败: {e}")
        return WorkflowResponse(
            status="error",
            message="工作流启动失败",
            error=str(e),
            timestamp=datetime.now(),
        )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_status(
    workflow_id: str,
    handler: WorkflowHandler = Depends(get_workflow_handler),
    user: Optional[str] = Depends(get_current_user),
) -> WorkflowResponse:
    """获取工作流状态"""
    try:
        state = await handler.get_workflow_status(workflow_id, user)
        if not state:
            return WorkflowResponse(
                status="error",
                message=f"工作流 {workflow_id} 不存在",
                workflow_id=workflow_id,
                error="Workflow not found",
                timestamp=datetime.now(),
            )

        return WorkflowResponse(
            status="success",
            message="获取工作流状态成功",
            workflow_id=workflow_id,
            data=state.to_dict(),
            timestamp=datetime.now(),
        )

    except WorkflowError as e:
        logger.error(f"获取工作流状态失败: {e}")
        return WorkflowResponse(
            status="error",
            message=str(e),
            workflow_id=workflow_id,
            error=str(e),
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}")
        return WorkflowResponse(
            status="error",
            message="获取工作流状态失败",
            workflow_id=workflow_id,
            error=str(e),
            timestamp=datetime.now(),
        )


@router.get("/{workflow_id}/progress", response_model=WorkflowResponse)
async def get_workflow_progress(
    workflow_id: str,
    handler: WorkflowHandler = Depends(get_workflow_handler),
    user: Optional[str] = Depends(get_current_user),
) -> WorkflowResponse:
    """获取工作流进度"""
    try:
        progress = await handler.get_progress(workflow_id)
        if not progress:
            return WorkflowResponse(
                status="error",
                message=f"工作流 {workflow_id} 不存在",
                workflow_id=workflow_id,
                error="Workflow not found",
                timestamp=datetime.now(),
            )

        return WorkflowResponse(
            status="success",
            message="获取工作流进度成功",
            workflow_id=workflow_id,
            data=progress,
            timestamp=datetime.now(),
        )

    except WorkflowError as e:
        logger.error(f"获取工作流进度失败: {e}")
        return WorkflowResponse(
            status="error",
            message=str(e),
            workflow_id=workflow_id,
            error=str(e),
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"获取工作流进度失败: {e}")
        return WorkflowResponse(
            status="error",
            message="获取工作流进度失败",
            workflow_id=workflow_id,
            error=str(e),
            timestamp=datetime.now(),
        )


@router.post("/{workflow_id}/step", response_model=WorkflowResponse)
async def execute_workflow_step(
    workflow_id: str,
    request: WorkflowStepRequest,
    handler: WorkflowHandler = Depends(get_workflow_handler),
    user: Optional[str] = Depends(get_current_user),
) -> WorkflowResponse:
    """执行工作流步骤"""
    try:
        result = await handler.execute_step(
            workflow_id=workflow_id,
            step_name=request.step_name,
            step_data=request.step_data,
            user_id=user,
        )

        return WorkflowResponse(
            status="success",
            message="工作流步骤执行成功",
            workflow_id=workflow_id,
            data=result,
            timestamp=datetime.now(),
        )

    except WorkflowError as e:
        logger.error(f"工作流步骤执行失败: {e}")
        return WorkflowResponse(
            status="error",
            message=str(e),
            workflow_id=workflow_id,
            error=str(e),
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"工作流步骤执行失败: {e}")
        return WorkflowResponse(
            status="error",
            message="工作流步骤执行失败",
            workflow_id=workflow_id,
            error=str(e),
            timestamp=datetime.now(),
        )


@router.delete("/{workflow_id}", response_model=WorkflowResponse)
async def terminate_workflow(
    workflow_id: str,
    handler: WorkflowHandler = Depends(get_workflow_handler),
    user: Optional[str] = Depends(get_current_user),
) -> WorkflowResponse:
    """终止工作流"""
    try:
        await handler.terminate_workflow(workflow_id)

        return WorkflowResponse(
            status="success",
            message="工作流终止成功",
            workflow_id=workflow_id,
            timestamp=datetime.now(),
        )

    except WorkflowError as e:
        logger.error(f"工作流终止失败: {e}")
        return WorkflowResponse(
            status="error",
            message=str(e),
            workflow_id=workflow_id,
            error=str(e),
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"工作流终止失败: {e}")
        return WorkflowResponse(
            status="error",
            message="工作流终止失败",
            workflow_id=workflow_id,
            error=str(e),
            timestamp=datetime.now(),
        )
