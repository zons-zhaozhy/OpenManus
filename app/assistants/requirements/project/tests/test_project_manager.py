# app/assistants/requirements/project/tests/test_project_manager.py

import asyncio
import unittest
from datetime import datetime
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock

from ..interfaces.event_publisher import IEventPublisher
from ..interfaces.storage import IProjectStorage, IRequirementStorage
from ..models.base import (
    Project,
    ProjectStatus,
    Requirement,
    RequirementStatus,
    RequirementType,
)
from ..services.project_manager import ProjectManager
from ..utils.exceptions import (
    DuplicateProjectError,
    DuplicateRequirementError,
    InvalidDependencyError,
    InvalidStatusTransitionError,
    ProjectNotFoundError,
    RequirementNotFoundError,
)
from ..utils.validators import ProjectValidator, RequirementValidator


# Define a concrete subclass for testing ProjectManager's abstract methods
class TestableProjectManager(ProjectManager):
    async def add_member(self, project_id: str, member_id: str, role: str) -> bool:
        return True

    async def remove_member(self, project_id: str, member_id: str) -> bool:
        return True

    async def update_member_role(
        self, project_id: str, member_id: str, new_role: str
    ) -> bool:
        return True

    async def update_project_settings(self, project_id: str, settings: dict) -> Project:
        # For simplicity, returning a mock project, or the test_project if available in context
        return Project(
            id=project_id,
            name="Mock Project",
            description="Mock Description",
            status=ProjectStatus.ACTIVE,
        )

    async def add_requirement(
        self, project_id: str, requirement: Requirement
    ) -> Requirement:
        # Simple implementation for testing purposes
        return requirement


class TestProjectManager(unittest.TestCase):
    """项目管理器测试类"""

    def setUp(self):
        """测试初始化"""
        # 创建mock对象
        self.project_storage = AsyncMock(spec=IProjectStorage)
        self.requirement_storage = AsyncMock(spec=IRequirementStorage)
        self.event_publisher = AsyncMock(spec=IEventPublisher)
        self.project_validator = MagicMock(spec=ProjectValidator)
        self.requirement_validator = MagicMock(spec=RequirementValidator)

        # Mock the `validate` method for both validators
        self.project_validator.validate.return_value = None
        self.requirement_validator.validate.return_value = None
        # Mock the `validate_requirement_transition` method for requirement_validator
        self.requirement_validator.validate_requirement_transition.return_value = True

        # 创建测试数据
        self.test_project = Project(
            id="test-project-1",
            name="Test Project",
            description="Test Project Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=ProjectStatus.ACTIVE,
        )

        self.test_requirement = Requirement(
            id="test-req-1",
            project_id=self.test_project.id,
            title="Test Requirement",
            description="Test Requirement Description",
            type=RequirementType.FUNCTIONAL,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=RequirementStatus.DRAFT,
            priority="high",
            dependencies=[],
        )

        # 创建项目管理器实例
        self.project_manager = TestableProjectManager(
            project_storage=self.project_storage,
            requirement_storage=self.requirement_storage,
            event_publisher=self.event_publisher,
            project_validator=self.project_validator,
            requirement_validator=self.requirement_validator,
        )

    def tearDown(self):
        """测试清理"""
        pass

    def test_create_project_success(self):
        """测试成功创建项目"""
        # Arrange
        self.project_storage.get_project.return_value = None
        self.project_storage.create_project.return_value = self.test_project

        # Act
        result = asyncio.run(self.project_manager.create_project(self.test_project))

        # Assert
        self.assertEqual(result, self.test_project)
        self.project_validator.validate.assert_called_once_with(self.test_project)
        self.project_storage.get_project.assert_called_once_with(self.test_project.id)
        self.project_storage.create_project.assert_called_once_with(self.test_project)
        self.event_publisher.publish_project_event.assert_called_once()

    def test_create_project_duplicate(self):
        """测试创建重复项目"""
        # Arrange
        self.project_storage.get_project.return_value = self.test_project

        # Act & Assert
        with self.assertRaises(DuplicateProjectError):
            asyncio.run(self.project_manager.create_project(self.test_project))

    def test_update_project_success(self):
        """测试成功更新项目"""
        # Arrange
        self.project_storage.get_project.return_value = self.test_project
        self.project_storage.update_project.return_value = self.test_project

        # Act
        result = asyncio.run(self.project_manager.update_project(self.test_project))

        # Assert
        self.assertEqual(result, self.test_project)
        self.project_validator.validate.assert_called_once_with(self.test_project)
        self.project_storage.get_project.assert_called_once_with(self.test_project.id)
        self.project_storage.update_project.assert_called_once_with(self.test_project)
        self.event_publisher.publish_project_event.assert_called_once()

    def test_update_project_not_found(self):
        """测试更新不存在的项目"""
        # Arrange
        self.project_storage.get_project.return_value = None

        # Act & Assert
        with self.assertRaises(ProjectNotFoundError):
            asyncio.run(self.project_manager.update_project(self.test_project))

    def test_delete_project_success(self):
        """测试成功删除项目"""
        # Arrange
        self.project_storage.get_project.return_value = self.test_project
        self.requirement_storage.list_requirements.return_value = []
        self.project_storage.delete_project.return_value = True

        # Act
        result = asyncio.run(self.project_manager.delete_project(self.test_project.id))

        # Assert
        self.assertTrue(result)
        self.project_storage.get_project.assert_called_once_with(self.test_project.id)
        self.requirement_storage.list_requirements.assert_called_once_with(
            self.test_project.id
        )
        self.project_storage.delete_project.assert_called_once_with(
            self.test_project.id
        )
        self.event_publisher.publish_project_event.assert_called_once()

    def test_delete_project_with_requirements(self):
        """测试删除带有需求的项目"""
        # Arrange
        self.project_storage.get_project.return_value = self.test_project
        self.requirement_storage.list_requirements.return_value = [
            self.test_requirement
        ]
        self.requirement_storage.delete_requirement.return_value = True
        self.project_storage.delete_project.return_value = True

        # Act
        result = asyncio.run(self.project_manager.delete_project(self.test_project.id))

        # Assert
        self.assertTrue(result)
        self.requirement_storage.delete_requirement.assert_called_once_with(
            self.test_requirement.id
        )

    def test_create_requirement_success(self):
        """测试成功创建需求"""
        # Arrange
        self.project_storage.get_project.return_value = self.test_project
        self.requirement_storage.get_requirement.return_value = None
        self.requirement_storage.create_requirement.return_value = self.test_requirement

        # Act
        result = asyncio.run(
            self.project_manager.create_requirement(self.test_requirement)
        )

        # Assert
        self.assertEqual(result, self.test_requirement)
        self.requirement_validator.validate.assert_called_once_with(
            self.test_requirement
        )
        self.project_storage.get_project.assert_called_once_with(self.test_project.id)
        self.requirement_storage.get_requirement.assert_called_once_with(
            self.test_requirement.id
        )
        self.requirement_storage.create_requirement.assert_called_once_with(
            self.test_requirement
        )
        self.event_publisher.publish_requirement_event.assert_called_once()

    def test_create_requirement_project_not_found(self):
        """测试在不存在的项目下创建需求"""
        # Arrange
        self.project_storage.get_project.return_value = None

        # Act & Assert
        with self.assertRaises(ProjectNotFoundError):
            asyncio.run(self.project_manager.create_requirement(self.test_requirement))

    def test_create_requirement_duplicate(self):
        """测试创建重复需求"""
        # Arrange
        self.project_storage.get_project.return_value = self.test_project
        self.requirement_storage.get_requirement.return_value = self.test_requirement

        # Act & Assert
        with self.assertRaises(DuplicateRequirementError):
            asyncio.run(self.project_manager.create_requirement(self.test_requirement))

    def test_update_requirement_success(self):
        """测试成功更新需求"""
        # Arrange
        self.requirement_storage.get_requirement.return_value = self.test_requirement
        self.project_storage.get_project.return_value = self.test_project
        self.requirement_storage.update_requirement.return_value = self.test_requirement
        self.requirement_validator.validate_requirement_dependencies.return_value = True

        # Act
        result = asyncio.run(
            self.project_manager.update_requirement(self.test_requirement)
        )

        # Assert
        self.assertEqual(result, self.test_requirement)
        self.requirement_validator.validate.assert_called_once_with(
            self.test_requirement
        )
        self.requirement_storage.get_requirement.assert_called_once_with(
            self.test_requirement.id
        )
        self.project_storage.get_project.assert_called_once_with(
            self.test_requirement.project_id
        )
        self.requirement_storage.update_requirement.assert_called_once_with(
            self.test_requirement
        )
        self.event_publisher.publish_requirement_event.assert_called_once()

    def test_update_requirement_not_found(self):
        """测试更新不存在的需求"""
        # Arrange
        self.requirement_storage.get_requirement.return_value = None

        # Act & Assert
        with self.assertRaises(RequirementNotFoundError):
            asyncio.run(self.project_manager.update_requirement(self.test_requirement))

    def test_update_requirement_project_not_found(self):
        """测试更新需求时项目不存在"""
        # Arrange
        self.requirement_storage.get_requirement.return_value = self.test_requirement
        self.project_storage.get_project.return_value = None

        # Act & Assert
        with self.assertRaises(ProjectNotFoundError):
            asyncio.run(self.project_manager.update_requirement(self.test_requirement))

    def test_update_requirement_invalid_dependency(self):
        """测试更新需求时依赖无效"""
        # Arrange
        self.requirement_storage.get_requirement.return_value = self.test_requirement
        self.project_storage.get_project.return_value = self.test_project
        self.requirement_validator.validate_requirement_dependencies.return_value = (
            False
        )

        # Act & Assert
        with self.assertRaises(InvalidDependencyError):
            asyncio.run(self.project_manager.update_requirement(self.test_requirement))

    def test_delete_requirement_success(self):
        """测试成功删除需求"""
        # Arrange
        self.requirement_storage.get_requirement.return_value = self.test_requirement
        self.requirement_storage.list_requirements.return_value = []
        self.requirement_storage.delete_requirement.return_value = True

        # Act
        result = asyncio.run(
            self.project_manager.delete_requirement(self.test_requirement.id)
        )

        # Assert
        self.assertTrue(result)
        self.requirement_storage.get_requirement.assert_called_once_with(
            self.test_requirement.id
        )
        self.requirement_storage.list_requirements.assert_called_once()  # Check for dependent requirements
        self.requirement_storage.delete_requirement.assert_called_once_with(
            self.test_requirement.id
        )
        self.event_publisher.publish_requirement_event.assert_called_once()

    def test_delete_requirement_not_found(self):
        """测试删除不存在的需求"""
        # Arrange
        self.requirement_storage.get_requirement.return_value = None

        # Act & Assert
        with self.assertRaises(RequirementNotFoundError):
            asyncio.run(
                self.project_manager.delete_requirement(self.test_requirement.id)
            )

    def test_delete_requirement_with_dependencies(self):
        """测试删除被依赖的需求"""
        # Arrange
        dependent_requirement = Requirement(
            id="test-req-2",
            project_id=self.test_project.id,
            title="Dependent Requirement",
            description="Dependent Requirement Description",
            type=RequirementType.FUNCTIONAL,
            status=RequirementStatus.DRAFT,
            priority="medium",
            dependencies=[self.test_requirement.id],
        )

        self.requirement_storage.get_requirement.side_effect = [
            self.test_requirement,  # For the requirement to be deleted
            dependent_requirement,  # For the dependent requirement check
        ]
        self.requirement_storage.list_requirements.return_value = [
            dependent_requirement
        ]  # Mock dependent requirements

        # Act & Assert
        with self.assertRaises(InvalidDependencyError):
            asyncio.run(
                self.project_manager.delete_requirement(self.test_requirement.id)
            )

    def test_get_project_success(self):
        """测试成功获取项目信息"""
        # Arrange
        self.project_storage.get_project.return_value = self.test_project

        # Act
        result = asyncio.run(self.project_manager.get_project(self.test_project.id))

        # Assert
        self.assertEqual(result, self.test_project)
        self.project_storage.get_project.assert_called_once_with(self.test_project.id)

    def test_get_project_not_found(self):
        """测试获取不存在的项目信息"""
        # Arrange
        self.project_storage.get_project.return_value = None

        # Act
        result = asyncio.run(self.project_manager.get_project(self.test_project.id))

        # Assert
        self.assertIsNone(result)

    def test_list_projects_success(self):
        """测试成功获取项目列表"""
        # Arrange
        self.project_storage.list_projects.return_value = [self.test_project]

        # Act
        result = asyncio.run(self.project_manager.list_projects())

        # Assert
        self.assertEqual(result, [self.test_project])
        self.project_storage.list_projects.assert_called_once()

    def test_get_requirement_success(self):
        """测试成功获取需求信息"""
        # Arrange
        self.requirement_storage.get_requirement.return_value = self.test_requirement

        # Act
        result = asyncio.run(
            self.project_manager.get_requirement(self.test_requirement.id)
        )

        # Assert
        self.assertEqual(result, self.test_requirement)
        self.requirement_storage.get_requirement.assert_called_once_with(
            self.test_requirement.id
        )

    def test_get_requirement_not_found(self):
        """测试获取不存在的需求信息"""
        # Arrange
        self.requirement_storage.get_requirement.return_value = None

        # Act
        result = asyncio.run(
            self.project_manager.get_requirement(self.test_requirement.id)
        )

        # Assert
        self.assertIsNone(result)

    def test_list_requirements_success(self):
        """测试成功获取项目下需求列表"""
        # Arrange
        self.requirement_storage.list_requirements.return_value = [
            self.test_requirement
        ]

        # Act
        result = asyncio.run(
            self.project_manager.list_requirements(self.test_project.id)
        )

        # Assert
        self.assertEqual(result, [self.test_requirement])
        self.requirement_storage.list_requirements.assert_called_once_with(
            self.test_project.id
        )

    def test_update_requirement_status_success(self):
        """测试成功更新需求状态"""
        # Arrange
        requirement = self.test_requirement
        new_status = RequirementStatus.IMPLEMENTED
        self.requirement_storage.get_requirement.return_value = requirement
        self.project_storage.get_project.return_value = (
            self.test_project
        )  # Ensure project is found
        self.requirement_validator.validate_requirement_transition.return_value = True
        updated_requirement = Requirement(
            id=requirement.id,
            project_id=requirement.project_id,
            title=requirement.title,
            description=requirement.description,
            type=requirement.type,
            priority=requirement.priority,
            status=new_status,  # Use the new status
            version=requirement.version,
            created_at=requirement.created_at,
            updated_at=datetime.now(),  # Update timestamp
            dependencies=requirement.dependencies,
            tags=requirement.tags,
            owner=requirement.owner,
            reviewers=requirement.reviewers,
        )
        self.requirement_storage.update_requirement.return_value = updated_requirement

        # Act
        result = asyncio.run(
            self.project_manager.update_requirement_status(
                self.test_requirement.id, new_status
            )
        )

        # Assert
        self.assertEqual(result.status, new_status)
        self.requirement_storage.get_requirement.assert_called_once_with(requirement.id)
        self.requirement_validator.validate_requirement_transition.assert_called_once_with(
            RequirementStatus.DRAFT,
            new_status,
            self.test_project.status,  # Use the initial status explicitly
        )
        self.requirement_storage.update_requirement.assert_called_once()
        self.event_publisher.publish_requirement_event.assert_called_once()

    def test_update_requirement_status_invalid_transition(self):
        """测试无效的需求状态转换"""
        # Arrange
        requirement = self.test_requirement
        new_status = RequirementStatus.IMPLEMENTED
        self.requirement_storage.get_requirement.return_value = requirement
        self.project_storage.get_project.return_value = (
            self.test_project
        )  # Ensure project is found
        self.requirement_validator.validate_requirement_transition.return_value = False

        # Act & Assert
        with self.assertRaises(InvalidStatusTransitionError):
            asyncio.run(
                self.project_manager.update_requirement_status(
                    self.test_requirement.id, new_status
                )
            )
        # Assert
        self.requirement_validator.validate_requirement_transition.assert_called_once_with(
            self.test_requirement.status,
            new_status,
            self.project_storage.get_project.return_value.status,  # Pass project status
        )
