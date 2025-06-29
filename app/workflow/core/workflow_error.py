"""
工作流错误类
"""

from typing import Any, Dict, List, Optional


class WorkflowError(Exception):
    """工作流错误基类"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class WorkflowValidationError(WorkflowError):
    """工作流验证错误"""

    pass


class WorkflowExecutionError(WorkflowError):
    """工作流执行错误"""

    pass


class WorkflowTimeoutError(WorkflowError):
    """工作流超时错误"""

    pass


class WorkflowStateError(WorkflowError):
    """工作流状态错误"""

    pass


class WorkflowConfigError(WorkflowError):
    """工作流配置错误"""

    pass


class WorkflowNotFoundError(WorkflowError):
    """工作流未找到错误"""

    pass
