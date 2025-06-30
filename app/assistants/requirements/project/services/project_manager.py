"""
项目管理器服务实现
"""

from typing import List, Optional

from ..interfaces.event_publisher import IEventPublisher
from ..interfaces.project_manager import IProjectManager
from ..interfaces.requirement_analyzer import IRequirementAnalyzer
from ..interfaces.storage import IProjectStorage, IRequirementStorage
from ..models.base import Project, Requirement
from ..services.requirement_analyzer import (
    RequirementAnalysis,
    Suggestion,
    ValidationResult,
)
from ..utils.events import (
    ProjectCreatedEvent,
    ProjectDeletedEvent,
    ProjectUpdatedEvent,
    RequirementCreatedEvent,
    RequirementDeletedEvent,
    RequirementStatusChangedEvent,
    RequirementUpdatedEvent,
)
from ..utils.exceptions import (
    DuplicateProjectError,
    DuplicateRequirementError,
    InvalidDependencyError,
    InvalidStatusTransitionError,
    ProjectNotFoundError,
    RequirementAnalysisError,
    RequirementNotFoundError,
)
from ..utils.validators import ProjectValidator, RequirementValidator


class ProjectManager(IProjectManager):
    """项目管理器服务实现"""

    def __init__(
        self,
        project_storage: IProjectStorage,
        requirement_storage: IRequirementStorage,
        event_publisher: IEventPublisher,
        requirement_analyzer: IRequirementAnalyzer,
        project_validator: ProjectValidator,
        requirement_validator: RequirementValidator,
    ):
        self._project_storage = project_storage
        self._requirement_storage = requirement_storage
        self._event_publisher = event_publisher
        self._requirement_analyzer = requirement_analyzer
        self._project_validator = project_validator
        self._requirement_validator = requirement_validator

    async def create_project(self, project: Project) -> Project:
        """创建新项目"""
        # 验证项目数据
        self._project_validator.validate(project)

        # 检查项目是否已存在
        existing_project = await self._project_storage.get_project(project.id)
        if existing_project:
            raise DuplicateProjectError(f"Project with id {project.id} already exists")

        # 创建项目
        created_project = await self._project_storage.create_project(project)

        # 发布事件
        await self._event_publisher.publish_project_event(
            ProjectCreatedEvent(project_id=created_project.id, project=created_project)
        )

        return created_project

    async def update_project(self, project: Project) -> Project:
        """更新项目信息"""
        # 验证项目数据
        self._project_validator.validate(project)

        # 检查项目是否存在
        old_project = await self._project_storage.get_project(project.id)
        if not old_project:
            raise ProjectNotFoundError(f"Project {project.id} not found")

        # 更新项目
        updated_project = await self._project_storage.update_project(project)

        # 发布事件
        await self._event_publisher.publish_project_event(
            ProjectUpdatedEvent(
                project_id=updated_project.id,
                old_project=old_project,
                new_project=updated_project,
            )
        )

        return updated_project

    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        # 检查项目是否存在
        project = await self._project_storage.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        # 删除项目下的所有需求
        requirements = await self._requirement_storage.list_requirements(project_id)
        for requirement in requirements:
            await self._requirement_storage.delete_requirement(requirement.id)

        # 删除项目
        result = await self._project_storage.delete_project(project_id)

        # 发布事件
        if result:
            await self._event_publisher.publish_project_event(
                ProjectDeletedEvent(project_id=project_id, project=project)
            )

        return result

    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目信息"""
        return await self._project_storage.get_project(project_id)

    async def list_projects(self) -> List[Project]:
        """获取所有项目列表"""
        return await self._project_storage.list_projects()

    async def create_requirement(self, requirement: Requirement) -> Requirement:
        """创建新需求"""
        # 验证需求数据
        self._requirement_validator.validate(requirement)

        # 检查项目是否存在
        project = await self._project_storage.get_project(requirement.project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {requirement.project_id} not found")

        # 检查需求是否已存在
        existing_requirement = await self._requirement_storage.get_requirement(
            requirement.id
        )
        if existing_requirement:
            raise DuplicateRequirementError(
                f"Requirement with id {requirement.id} already exists"
            )

        # 检查依赖需求是否存在并验证循环依赖
        all_requirements = await self._requirement_storage.list_requirements(
            requirement.project_id
        )
        # Temporarily add the new requirement to the list for validation, then remove it
        temp_all_requirements = all_requirements + [requirement]
        if not self._requirement_validator.validate_requirement_dependencies(
            requirement, temp_all_requirements
        ):
            raise InvalidDependencyError(
                "Circular dependency detected or invalid dependency"
            )

        # 检查依赖需求是否存在
        for dep_id in requirement.dependencies:
            dep = await self._requirement_storage.get_requirement(dep_id)
            if not dep:
                raise InvalidDependencyError(
                    f"Dependency requirement {dep_id} not found"
                )
            if dep.project_id != requirement.project_id:
                raise InvalidDependencyError(
                    f"Dependency requirement {dep_id} belongs to different project"
                )

        # 创建需求
        created_requirement = await self._requirement_storage.create_requirement(
            requirement
        )

        # 发布事件
        await self._event_publisher.publish_requirement_event(
            RequirementCreatedEvent(
                requirement_id=created_requirement.id,
                project_id=created_requirement.project_id,
                requirement=created_requirement,
            )
        )

        return created_requirement

    async def update_requirement(self, requirement: Requirement) -> Requirement:
        """更新需求信息"""
        # 验证需求数据
        self._requirement_validator.validate(requirement)

        # 检查需求是否存在
        old_requirement = await self._requirement_storage.get_requirement(
            requirement.id
        )
        if not old_requirement:
            raise RequirementNotFoundError(f"Requirement {requirement.id} not found")

        # 检查项目是否存在
        project = await self._project_storage.get_project(requirement.project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {requirement.project_id} not found")

        # 检查依赖需求是否存在并验证循环依赖
        all_requirements = await self._requirement_storage.list_requirements(
            requirement.project_id
        )
        # Filter out the old requirement and add the updated one for validation
        filtered_requirements = [
            r for r in all_requirements if r.id != old_requirement.id
        ] + [requirement]
        if not self._requirement_validator.validate_requirement_dependencies(
            requirement, filtered_requirements
        ):
            raise InvalidDependencyError(
                "Circular dependency detected or invalid dependency"
            )

        # 检查依赖需求是否存在
        for dep_id in requirement.dependencies:
            dep = await self._requirement_storage.get_requirement(dep_id)
            if not dep:
                raise InvalidDependencyError(
                    f"Dependency requirement {dep_id} not found"
                )
            if dep.project_id != requirement.project_id:
                raise InvalidDependencyError(
                    f"Dependency requirement {dep_id} belongs to different project"
                )

        # 更新需求
        updated_requirement = await self._requirement_storage.update_requirement(
            requirement
        )

        # 发布事件
        await self._event_publisher.publish_requirement_event(
            RequirementUpdatedEvent(
                requirement_id=updated_requirement.id,
                project_id=updated_requirement.project_id,
                old_requirement=old_requirement,
                new_requirement=updated_requirement,
            )
        )

        # 如果状态发生变化，发布状态变更事件
        if old_requirement.status != updated_requirement.status:
            await self._event_publisher.publish_requirement_event(
                RequirementStatusChangedEvent(
                    requirement_id=updated_requirement.id,
                    project_id=updated_requirement.project_id,
                    old_status=old_requirement.status,
                    new_status=updated_requirement.status,
                    requirement=updated_requirement,
                )
            )

        return updated_requirement

    async def delete_requirement(self, requirement_id: str) -> bool:
        """删除需求"""
        # 检查需求是否存在
        requirement = await self._requirement_storage.get_requirement(requirement_id)
        if not requirement:
            raise RequirementNotFoundError(f"Requirement {requirement_id} not found")

        # 检查是否有其他需求依赖于此需求
        all_requirements = await self._requirement_storage.list_requirements(
            requirement.project_id
        )
        for req in all_requirements:
            if req.dependencies and requirement_id in req.dependencies:
                raise InvalidDependencyError(
                    f"Cannot delete requirement {requirement_id} as it is depended on by {req.id}"
                )

        # 删除需求
        result = await self._requirement_storage.delete_requirement(requirement_id)

        # 发布事件
        if result:
            await self._event_publisher.publish_requirement_event(
                RequirementDeletedEvent(
                    requirement_id=requirement_id,
                    project_id=requirement.project_id,
                    requirement=requirement,
                )
            )

        return result

    async def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """获取需求信息"""
        return await self._requirement_storage.get_requirement(requirement_id)

    async def list_requirements(self, project_id: str) -> List[Requirement]:
        """获取项目下的所有需求列表"""
        # 检查项目是否存在
        project = await self._project_storage.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        return await self._requirement_storage.list_requirements(project_id)

    async def get_requirements_by_status(
        self, project_id: str, status: str
    ) -> List[Requirement]:
        """获取项目下指定状态的需求列表"""
        # 检查项目是否存在
        project = await self._project_storage.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        return await self._requirement_storage.get_requirements_by_status(
            project_id, status
        )

    async def update_requirement_status(
        self, requirement_id: str, new_status: str
    ) -> Requirement:
        """更新需求状态"""
        requirement = await self._requirement_storage.get_requirement(requirement_id)
        if not requirement:
            raise RequirementNotFoundError(f"Requirement {requirement_id} not found")

        project = await self._project_storage.get_project(requirement.project_id)
        if not project:
            # This case should ideally not happen if requirement exists and has a project_id
            # but for robustness, we include it.
            raise ProjectNotFoundError(
                f"Project {requirement.project_id} not found for requirement {requirement_id}"
            )

        if not self._requirement_validator.validate_requirement_transition(
            requirement.status, new_status, project.status
        ):
            raise InvalidStatusTransitionError(
                f"Invalid status transition from {requirement.status} to {new_status}"
            )

        # Update the requirement status
        old_status = requirement.status
        requirement.status = new_status
        updated_requirement = await self._requirement_storage.update_requirement(
            requirement
        )

        # Publish the event
        await self._event_publisher.publish_requirement_event(
            RequirementStatusChangedEvent(
                requirement_id=updated_requirement.id,
                project_id=updated_requirement.project_id,
                old_status=old_status,
                new_status=new_status,
                requirement=updated_requirement,
            )
        )

        return updated_requirement

    async def analyze_requirement_text(self, text: str) -> RequirementAnalysis:
        """分析需求文本"""
        try:
            return await self._requirement_analyzer.analyze_requirement(text)
        except Exception as e:
            raise RequirementAnalysisError(
                f"Failed to analyze requirement text: {str(e)}"
            )

    async def validate_requirement_quality(
        self, requirement_id: str
    ) -> ValidationResult:
        """验证需求质量"""
        requirement = await self.get_requirement(requirement_id)
        if not requirement:
            raise RequirementNotFoundError(f"Requirement {requirement_id} not found")

        try:
            return await self._requirement_analyzer.validate_requirement(requirement)
        except Exception as e:
            raise RequirementAnalysisError(f"Failed to validate requirement: {str(e)}")

    async def get_requirement_improvements(
        self, requirement_id: str
    ) -> List[Suggestion]:
        """获取需求改进建议"""
        requirement = await self.get_requirement(requirement_id)
        if not requirement:
            raise RequirementNotFoundError(f"Requirement {requirement_id} not found")

        try:
            return await self._requirement_analyzer.suggest_improvements(requirement)
        except Exception as e:
            raise RequirementAnalysisError(
                f"Failed to get requirement improvements: {str(e)}"
            )

    async def create_requirement_from_analysis(
        self, project_id: str, analysis: RequirementAnalysis
    ) -> Requirement:
        """从分析结果创建需求"""
        # 检查项目是否存在
        project = await self._project_storage.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        # 创建需求对象
        requirement = Requirement(
            project_id=project_id,
            description="\n".join(analysis.requirement_points),
            priority=analysis.priority,
            status="new",
            dependencies=analysis.dependencies,
            acceptance_criteria=analysis.acceptance_criteria,
            risk_points=analysis.risk_points,
            type=analysis.requirement_type,
        )

        # 创建需求
        return await self.create_requirement(requirement)
