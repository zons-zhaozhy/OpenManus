"""
项目管理器接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ..models.base import Project, Requirement
from ..services.requirement_analyzer import (
    RequirementAnalysis,
    Suggestion,
    ValidationResult,
)


class IProjectManager(ABC):
    """项目管理器接口"""

    @abstractmethod
    async def create_project(self, project: Project) -> Project:
        """创建新项目"""
        pass

    @abstractmethod
    async def update_project(self, project: Project) -> Project:
        """更新项目信息"""
        pass

    @abstractmethod
    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        pass

    @abstractmethod
    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目信息"""
        pass

    @abstractmethod
    async def list_projects(self) -> List[Project]:
        """获取所有项目列表"""
        pass

    @abstractmethod
    async def create_requirement(self, requirement: Requirement) -> Requirement:
        """创建新需求"""
        pass

    @abstractmethod
    async def update_requirement(self, requirement: Requirement) -> Requirement:
        """更新需求信息"""
        pass

    @abstractmethod
    async def delete_requirement(self, requirement_id: str) -> bool:
        """删除需求"""
        pass

    @abstractmethod
    async def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """获取需求信息"""
        pass

    @abstractmethod
    async def list_requirements(self, project_id: str) -> List[Requirement]:
        """获取项目的所有需求列表"""
        pass

    @abstractmethod
    async def get_requirements_by_status(
        self, project_id: str, status: str
    ) -> List[Requirement]:
        """获取指定状态的需求列表"""
        pass

    @abstractmethod
    async def update_requirement_status(
        self, requirement_id: str, new_status: str
    ) -> Requirement:
        """更新需求状态"""
        pass

    @abstractmethod
    async def analyze_requirement_text(self, text: str) -> RequirementAnalysis:
        """分析需求文本"""
        pass

    @abstractmethod
    async def validate_requirement_quality(
        self, requirement_id: str
    ) -> ValidationResult:
        """验证需求质量"""
        pass

    @abstractmethod
    async def get_requirement_improvements(
        self, requirement_id: str
    ) -> List[Suggestion]:
        """获取需求改进建议"""
        pass

    @abstractmethod
    async def create_requirement_from_analysis(
        self, project_id: str, analysis: RequirementAnalysis
    ) -> Requirement:
        """从分析结果创建需求"""
        pass

    @abstractmethod
    async def add_member(self, project_id: str, member_id: str, role: str) -> bool:
        """添加成员"""
        pass

    @abstractmethod
    async def remove_member(self, project_id: str, member_id: str) -> bool:
        """移除成员"""
        pass

    @abstractmethod
    async def update_member_role(
        self, project_id: str, member_id: str, new_role: str
    ) -> bool:
        """更新成员角色"""
        pass

    @abstractmethod
    async def update_project_settings(self, project_id: str, settings: Dict) -> Project:
        """更新项目设置"""
        pass
