"""
验证工具类
"""

from typing import Any, List, Optional

from ..models.base import Project, ProjectStatus, Requirement, RequirementStatus


class ProjectValidator:
    """项目验证器"""

    @staticmethod
    def validate(project: Project) -> None:
        """
        通用项目验证方法。
        """
        # TODO: Implement actual project validation logic here
        pass

    @staticmethod
    def validate_project_transition(
        current_status: ProjectStatus, target_status: ProjectStatus
    ) -> bool:
        """
        验证项目状态转换是否有效

        Args:
            current_status: 当前状态
            target_status: 目标状态

        Returns:
            bool: 状态转换是否有效
        """
        # 定义有效的状态转换
        valid_transitions = {
            ProjectStatus.DRAFT: [ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED],
            ProjectStatus.ACTIVE: [
                ProjectStatus.PAUSED,
                ProjectStatus.COMPLETED,
                ProjectStatus.ARCHIVED,
            ],
            ProjectStatus.PAUSED: [ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED],
            ProjectStatus.COMPLETED: [ProjectStatus.ARCHIVED],
            ProjectStatus.ARCHIVED: [],  # 归档状态不能转换到其他状态
        }

        return target_status in valid_transitions.get(current_status, [])

    @staticmethod
    def validate_project_completion(project: Project) -> bool:
        """
        验证项目是否可以完成

        Args:
            project: 项目对象

        Returns:
            bool: 是否可以完成
        """
        # 检查是否有未完成的需求
        return all(
            requirement.status
            in [
                RequirementStatus.IMPLEMENTED,
                RequirementStatus.VERIFIED,
                RequirementStatus.REJECTED,
            ]
            for requirement in project.requirements
        )


class RequirementValidator:
    """需求验证器"""

    @staticmethod
    def validate(requirement: Requirement) -> None:
        """
        通用需求验证方法。
        """
        # TODO: Implement actual requirement validation logic here
        pass

    @staticmethod
    def validate_requirement_transition(
        current_status: RequirementStatus,
        target_status: RequirementStatus,
        project_status: ProjectStatus,
    ) -> bool:
        """
        验证需求状态转换是否有效

        Args:
            current_status: 当前状态
            target_status: 目标状态
            project_status: 项目状态

        Returns:
            bool: 状态转换是否有效
        """
        # 如果项目已归档，不允许任何状态转换
        if project_status == ProjectStatus.ARCHIVED:
            return False

        # 定义有效的状态转换
        valid_transitions = {
            RequirementStatus.DRAFT: [
                RequirementStatus.REVIEW,
                RequirementStatus.REJECTED,
            ],
            RequirementStatus.REVIEW: [
                RequirementStatus.APPROVED,
                RequirementStatus.REJECTED,
                RequirementStatus.DRAFT,
            ],
            RequirementStatus.APPROVED: [
                RequirementStatus.IMPLEMENTED,
                RequirementStatus.REVIEW,
            ],
            RequirementStatus.IMPLEMENTED: [
                RequirementStatus.VERIFIED,
                RequirementStatus.REVIEW,
            ],
            RequirementStatus.VERIFIED: [],  # 验证通过的需求不能改变状态
            RequirementStatus.REJECTED: [RequirementStatus.DRAFT],
        }

        return target_status in valid_transitions.get(current_status, [])

    @staticmethod
    def validate_requirement_dependencies(
        requirement: Requirement, all_requirements: List[Requirement]
    ) -> bool:
        """
        验证需求依赖关系是否有效

        Args:
            requirement: 需求对象
            all_requirements: 所有需求列表

        Returns:
            bool: 依赖关系是否有效
        """
        # 检查是否存在循环依赖
        visited = set()

        def has_cycle(req_id: str, path: set) -> bool:
            if req_id in path:
                return True
            if req_id in visited:
                return False

            visited.add(req_id)
            path.add(req_id)

            # 获取当前需求对象
            current_req = next((r for r in all_requirements if r.id == req_id), None)
            if not current_req:
                return False

            # 递归检查所有依赖
            for dep_id in current_req.dependencies:
                if has_cycle(dep_id, path.copy()):
                    return True

            return False

        return not has_cycle(requirement.id, set())
