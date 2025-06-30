"""
项目管理相关异常类
"""

from typing import Any, Optional


class ProjectError(Exception):
    """项目管理基础异常类"""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.details = details


class ProjectNotFoundError(ProjectError):
    """项目不存在异常"""

    pass


class RequirementNotFoundError(ProjectError):
    """需求不存在异常"""

    pass


class InvalidStatusTransitionError(ProjectError):
    """状态转换无效异常"""

    pass


class DuplicateProjectError(ProjectError):
    """项目重复异常"""

    pass


class DuplicateRequirementError(ProjectError):
    """需求重复异常"""

    pass


class InvalidDependencyError(ProjectError):
    """无效依赖异常"""

    pass


class MemberNotFoundError(ProjectError):
    """成员不存在异常"""

    pass


class ValidationError(ProjectError):
    """验证失败异常"""

    pass


class StorageError(ProjectError):
    """存储操作异常"""

    pass


class RequirementError(Exception):
    """需求相关错误的基类"""

    pass


class RequirementAnalysisError(RequirementError):
    """需求分析错误"""

    pass


class RequirementValidationError(RequirementError):
    """需求验证错误"""

    pass


class RequirementImprovementError(RequirementError):
    """需求改进建议生成错误"""

    pass
