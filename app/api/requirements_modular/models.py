"""
数据模型 - 从原始API完全复制，保持接口一致性
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.workflow.core.workflow_error import WorkflowError
from app.workflow.core.workflow_state import WorkflowState as CoreWorkflowState
from app.workflow.core.workflow_step import WorkflowStep as CoreWorkflowStep


class RequirementInput(BaseModel):
    content: str
    project_id: Optional[str] = None  # 项目制管理支持
    project_context: Optional[str] = None
    use_multi_dimensional: Optional[bool] = True  # 默认启用多维度分析
    enable_conflict_detection: Optional[bool] = True  # 默认启用冲突检测


class ClarificationRequest(BaseModel):
    session_id: str
    answer: str
    question: Optional[str] = None


class ClarificationResponse(BaseModel):
    session_id: str
    status: str
    response: str
    next_questions: Optional[List[str]] = None
    final_report: Optional[Dict] = None
    progress: Optional[Dict] = None


class AnalysisRequest(BaseModel):
    session_id: str
    answer: str


class RequirementStatus(BaseModel):
    session_id: str
    stage: str
    progress: Dict
    result: Optional[str] = None


class WorkflowContext(BaseModel):
    """工作流上下文"""

    workflow_id: str = Field(..., description="工作流ID")
    project_id: str = Field(..., description="项目ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    initial_requirements: str = Field(..., description="初始需求")
    project_context: Optional[str] = Field(None, description="项目上下文")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "workflow_id": self.workflow_id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "initial_requirements": self.initial_requirements,
            "project_context": self.project_context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkflowStep(CoreWorkflowStep):
    """工作流步骤 - 继承自核心模型"""

    pass


class WorkflowState(CoreWorkflowState):
    """工作流状态 - 继承自核心模型"""

    pass


class WorkflowError(Exception):
    """工作流异常"""

    pass


class WorkflowResponse(BaseModel):
    """工作流响应"""

    status: str = Field(..., description="响应状态")
    message: str = Field(..., description="响应消息")
    workflow_id: Optional[str] = Field(None, description="工作流ID")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status,
            "message": self.message,
            "workflow_id": self.workflow_id,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }
