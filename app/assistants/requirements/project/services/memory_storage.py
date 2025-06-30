"""
基于内存的项目管理存储实现
"""

from typing import Dict, List, Optional

from ..interfaces.storage import IProjectStorage, IRequirementStorage
from ..models.base import Project, Requirement
from ..utils.exceptions import ProjectNotFoundError, RequirementNotFoundError


class MemoryProjectStorage(IProjectStorage):
    """基于内存的项目存储实现"""

    def __init__(self):
        self._projects: Dict[str, Project] = {}

    async def create_project(self, project: Project) -> Project:
        """创建项目"""
        self._projects[project.id] = project
        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        return self._projects.get(project_id)

    async def update_project(self, project: Project) -> Project:
        """更新项目"""
        if project.id not in self._projects:
            raise ProjectNotFoundError(f"Project {project.id} not found")
        self._projects[project.id] = project
        return project

    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        if project_id not in self._projects:
            return False
        del self._projects[project_id]
        return True

    async def list_projects(self) -> List[Project]:
        """列出所有项目"""
        return list(self._projects.values())


class MemoryRequirementStorage(IRequirementStorage):
    """基于内存的需求存储实现"""

    def __init__(self):
        self._requirements: Dict[str, Requirement] = {}

    async def create_requirement(self, requirement: Requirement) -> Requirement:
        """创建需求"""
        self._requirements[requirement.id] = requirement
        return requirement

    async def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """获取需求"""
        return self._requirements.get(requirement_id)

    async def update_requirement(self, requirement: Requirement) -> Requirement:
        """更新需求"""
        if requirement.id not in self._requirements:
            raise RequirementNotFoundError(f"Requirement {requirement.id} not found")
        self._requirements[requirement.id] = requirement
        return requirement

    async def delete_requirement(self, requirement_id: str) -> bool:
        """删除需求"""
        if requirement_id not in self._requirements:
            return False
        del self._requirements[requirement_id]
        return True

    async def list_requirements(self, project_id: str) -> List[Requirement]:
        """列出项目下所有需求"""
        return [
            req for req in self._requirements.values() if req.project_id == project_id
        ]

    async def get_requirements_by_status(
        self, project_id: str, status: str
    ) -> List[Requirement]:
        """获取指定状态的需求"""
        return [
            req
            for req in self._requirements.values()
            if req.project_id == project_id and req.status == status
        ]
