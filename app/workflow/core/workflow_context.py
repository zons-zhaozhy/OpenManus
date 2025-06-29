"""
工作流上下文

提供工作流执行过程中的上下文信息
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WorkflowContext(BaseModel):
    """工作流上下文"""

    workflow_id: str = Field(..., description="工作流ID")
    execution_id: str = Field(..., description="执行ID")
    status: str = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    current_step: Optional[str] = Field(None, description="当前执行步骤")
    data: Dict = Field(default_factory=dict, description="上下文数据")
    metadata: Dict = Field(default_factory=dict, description="上下文元数据")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_step": self.current_step,
            "data": self.data,
            "metadata": self.metadata,
            "error": self.error,
        }
