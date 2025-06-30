from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.base import Project, Requirement


class IProjectStorage(ABC):
    """项目存储接口"""

    @abstractmethod
    async def create_project(self, project: Project) -> Project:
        """创建项目"""
        pass

    @abstractmethod
    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        pass

    @abstractmethod
    async def update_project(self, project: Project) -> Project:
        """更新项目"""
        pass

    @abstractmethod
    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        pass

    @abstractmethod
    async def list_projects(self) -> List[Project]:
        """列出所有项目"""
        pass


class IRequirementStorage(ABC):
    """需求存储接口"""

    @abstractmethod
    async def create_requirement(self, requirement: Requirement) -> Requirement:
        """创建需求"""
        pass

    @abstractmethod
    async def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """获取需求"""
        pass

    @abstractmethod
    async def update_requirement(self, requirement: Requirement) -> Requirement:
        """更新需求"""
        pass

    @abstractmethod
    async def delete_requirement(self, requirement_id: str) -> bool:
        """删除需求"""
        pass

    @abstractmethod
    async def list_requirements(self, project_id: str) -> List[Requirement]:
        """列出项目下的所有需求"""
        pass
