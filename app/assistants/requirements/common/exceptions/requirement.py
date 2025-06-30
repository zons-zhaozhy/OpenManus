"""
需求分析相关异常类
"""


class RequirementError(Exception):
    """需求相关错误的基类"""

    pass


class RequirementAnalysisError(RequirementError):
    """需求分析过程中的错误"""

    pass


class RequirementValidationError(RequirementError):
    """需求验证过程中的错误"""

    pass


class RequirementConflictError(RequirementError):
    """需求冲突相关的错误"""

    pass
