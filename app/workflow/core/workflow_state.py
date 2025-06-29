"""
工作流状态定义

提供工作流状态的数据模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowState(BaseModel):
    """工作流状态"""

    id: str = Field(..., description="工作流ID")
    type: str = Field(..., description="工作流类型")
    status: str = Field(..., description="执行状态")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    current_step: Optional[str] = Field(None, description="当前步骤")
    steps_completed: List[str] = Field(default_factory=list, description="已完成步骤")
    steps_remaining: List[str] = Field(default_factory=list, description="剩余步骤")
    data: Dict[str, Any] = Field(default_factory=dict, description="工作流数据")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="工作流元数据")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_step": self.current_step,
            "steps_completed": self.steps_completed,
            "steps_remaining": self.steps_remaining,
            "data": self.data,
            "metadata": self.metadata,
            "error": self.error,
        }
