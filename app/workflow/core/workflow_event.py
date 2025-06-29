"""
工作流事件定义
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class WorkflowEvent(BaseModel):
    """工作流事件"""

    type: str = Field(..., description="事件类型")
    workflow_id: str = Field(..., description="工作流ID")
    execution_id: Optional[str] = Field(None, description="执行ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件时间戳")
    data: Dict = Field(default_factory=dict, description="事件数据")
    metadata: Dict = Field(default_factory=dict, description="事件元数据")

    class Config:
        arbitrary_types_allowed = True
