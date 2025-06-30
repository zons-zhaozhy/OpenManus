"""
项目管理相关事件类
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from ..models.base import Project, Requirement


@dataclass(kw_only=True)
class ProjectEvent:
    """项目事件基类"""

    project_id: str
    timestamp: datetime = datetime.now()
    details: Optional[Dict[str, Any]] = None


@dataclass(kw_only=True)
class ProjectCreatedEvent(ProjectEvent):
    """项目创建事件"""

    project: Project


@dataclass(kw_only=True)
class ProjectUpdatedEvent(ProjectEvent):
    """项目更新事件"""

    old_project: Project
    new_project: Project


@dataclass(kw_only=True)
class ProjectDeletedEvent(ProjectEvent):
    """项目删除事件"""

    project: Project


@dataclass(kw_only=True)
class RequirementEvent:
    """需求事件基类"""

    requirement_id: str
    project_id: str
    timestamp: datetime = datetime.now()
    details: Optional[Dict[str, Any]] = None


@dataclass(kw_only=True)
class RequirementCreatedEvent(RequirementEvent):
    """需求创建事件"""

    requirement: Requirement


@dataclass(kw_only=True)
class RequirementUpdatedEvent(RequirementEvent):
    """需求更新事件"""

    old_requirement: Requirement
    new_requirement: Requirement


@dataclass(kw_only=True)
class RequirementDeletedEvent(RequirementEvent):
    """需求删除事件"""

    requirement: Requirement


@dataclass(kw_only=True)
class RequirementStatusChangedEvent(RequirementEvent):
    """需求状态变更事件"""

    old_status: str
    new_status: str
    requirement: Requirement
