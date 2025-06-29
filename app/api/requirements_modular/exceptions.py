"""
需求分析模块异常类

定义所有需求分析相关的自定义异常
"""

from typing import Optional


class RequirementAnalysisError(Exception):
    """需求分析基础异常类"""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class SessionError(RequirementAnalysisError):
    """会话相关异常"""

    pass


class InvalidSessionError(SessionError):
    """无效的会话ID"""

    pass


class SessionExpiredError(SessionError):
    """会话已过期"""

    pass


class AnalysisError(RequirementAnalysisError):
    """分析过程异常"""

    pass


class AnalysisTimeoutError(AnalysisError):
    """分析超时"""

    pass


class InvalidInputError(AnalysisError):
    """无效的输入数据"""

    pass


class ClarificationError(RequirementAnalysisError):
    """需求澄清异常"""

    pass


class WorkflowError(RequirementAnalysisError):
    """工作流程异常"""

    pass


class StorageError(RequirementAnalysisError):
    """存储相关异常"""

    pass


class PerformanceError(RequirementAnalysisError):
    """性能相关异常"""

    pass
