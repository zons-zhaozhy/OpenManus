"""
基础数据模型定义
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """项目状态枚举"""

    DRAFT = "draft"  # 草稿
    ACTIVE = "active"  # 活动
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 完成
    ARCHIVED = "archived"  # 归档


class RequirementType(str, Enum):
    """需求类型枚举"""

    FUNCTIONAL = "functional"  # 功能需求
    NON_FUNCTIONAL = "non_functional"  # 非功能需求
    BUSINESS = "business"  # 业务需求
    USER = "user"  # 用户需求
    SYSTEM = "system"  # 系统需求


class Priority(str, Enum):
    """优先级枚举"""

    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    URGENT = "urgent"  # 紧急


class RequirementStatus(str, Enum):
    """需求状态枚举"""

    DRAFT = "draft"  # 草稿
    REVIEW = "review"  # 评审中
    APPROVED = "approved"  # 已批准
    IMPLEMENTED = "implemented"  # 已实现
    VERIFIED = "verified"  # 已验证
    REJECTED = "rejected"  # 已拒绝


class Member(BaseModel):
    """团队成员模型"""

    id: str = Field(..., description="成员ID")
    name: str = Field(..., description="成员名称")
    role: str = Field(..., description="成员角色")
    email: Optional[str] = Field(None, description="成员邮箱")


class ProjectSettings(BaseModel):
    """项目设置模型"""

    template: str = Field("standard", description="项目模板")
    language: str = Field("zh_CN", description="项目语言")
    naming_convention: str = Field("REQ-{project}-{number}", description="需求命名规范")
    version_format: str = Field("v{major}.{minor}", description="版本格式")
    status_flow: List[str] = Field(
        ["draft", "review", "approved", "implemented"], description="状态流转"
    )
    quality_settings: dict = Field(
        default_factory=lambda: {
            "min_completeness_score": 0.8,
            "min_consistency_score": 0.9,
            "required_fields": ["description", "priority", "owner"],
        },
        description="质量设置",
    )


class Project(BaseModel):
    """项目模型"""

    id: str = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: ProjectStatus = Field(ProjectStatus.DRAFT, description="项目状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    members: List[Member] = Field(default_factory=list, description="项目成员")
    settings: ProjectSettings = Field(
        default_factory=ProjectSettings, description="项目设置"
    )


class Requirement(BaseModel):
    """需求模型"""

    id: str = Field(..., description="需求ID")
    project_id: str = Field(..., description="所属项目ID")
    description: str = Field(..., description="需求描述")
    type: str = Field("functional", description="需求类型（功能性/非功能性）")
    priority: str = Field(..., description="优先级（高/中/低）")
    status: str = Field(..., description="状态")
    dependencies: List[str] = Field(
        default_factory=list, description="依赖的其他需求ID"
    )
    acceptance_criteria: List[str] = Field(default_factory=list, description="验收标准")
    risk_points: List[str] = Field(default_factory=list, description="风险点")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        """模型配置"""

        json_encoders = {datetime: lambda v: v.isoformat()}
