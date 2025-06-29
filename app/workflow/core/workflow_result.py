"""
工作流结果定义
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class WorkflowResult(BaseModel):
    """工作流执行结果"""

    workflow_id: str = Field(..., description="工作流ID")
    execution_id: str = Field(..., description="执行ID")
    status: str = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    data: Dict = Field(default_factory=dict, description="结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Dict = Field(default_factory=dict, description="结果元数据")

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }

    @property
    def duration(self) -> float:
        """计算执行时长（秒）"""
        return (self.end_time - self.start_time).total_seconds()
