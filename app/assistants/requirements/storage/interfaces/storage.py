"""
需求存储接口定义
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ...common.models.requirement import Requirement


class IRequirementStorage(ABC):
    """需求存储接口"""

    @abstractmethod
    async def create_requirement(self, requirement: Requirement) -> str:
        """创建新需求

        Args:
            requirement: 需求对象

        Returns:
            str: 需求ID
        """
        pass

    @abstractmethod
    async def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """获取需求

        Args:
            requirement_id: 需求ID

        Returns:
            Optional[Requirement]: 需求对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def update_requirement(self, requirement: Requirement) -> bool:
        """更新需求

        Args:
            requirement: 需求对象

        Returns:
            bool: 更新是否成功
        """
        pass

    @abstractmethod
    async def delete_requirement(self, requirement_id: str) -> bool:
        """删除需求

        Args:
            requirement_id: 需求ID

        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    async def list_requirements(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[Requirement]:
        """列出需求

        Args:
            project_id: 项目ID
            status: 需求状态
            priority: 需求优先级

        Returns:
            List[Requirement]: 需求列表
        """
        pass
