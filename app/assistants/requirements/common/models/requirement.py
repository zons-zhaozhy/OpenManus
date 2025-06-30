"""
需求模型定义
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Requirement(BaseModel):
    """需求模型"""

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
        extra="forbid",
    )

    id: str = Field(description="需求ID")
    title: str = Field(description="需求标题")
    description: str = Field(description="需求描述")
    priority: str = Field(description="优先级", pattern="^(high|medium|low)$")
    status: str = Field(
        description="状态",
        pattern="^(draft|review|approved|rejected|implemented|verified)$",
    )
    type: str = Field(description="类型", pattern="^(functional|non_functional)$")
    dependencies: List[str] = Field(
        default_factory=list, description="依赖的需求ID列表"
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list, description="验收标准列表"
    )
    project_id: str = Field(description="所属项目ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    created_by: str = Field(description="创建者")
    updated_by: str = Field(description="更新者")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    attachments: List[str] = Field(default_factory=list, description="附件列表")
    comments: List[str] = Field(default_factory=list, description="评论ID列表")
    version: int = Field(default=1, description="版本号")
    parent_id: Optional[str] = Field(default=None, description="父需求ID")
    children: List[str] = Field(default_factory=list, description="子需求ID列表")
    estimated_effort: Optional[float] = Field(
        default=None, description="预估工作量(人天)"
    )
    actual_effort: Optional[float] = Field(default=None, description="实际工作量(人天)")
    deadline: Optional[datetime] = Field(default=None, description="截止时间")
    assignee: Optional[str] = Field(default=None, description="负责人")
    reviewer: Optional[str] = Field(default=None, description="审核人")
    risk_level: Optional[str] = Field(
        default=None, description="风险等级", pattern="^(high|medium|low)$"
    )
    business_value: Optional[str] = Field(
        default=None, description="业务价值", pattern="^(high|medium|low)$"
    )
    source: Optional[str] = Field(default=None, description="需求来源")
    rationale: Optional[str] = Field(default=None, description="需求理由")
    assumptions: List[str] = Field(default_factory=list, description="假设条件列表")
    constraints: List[str] = Field(default_factory=list, description="约束条件列表")
    stakeholders: List[str] = Field(default_factory=list, description="干系人列表")
