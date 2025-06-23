"""
OpenManus API模块

提供前端与后端智能体之间的API接口。
"""

from .architecture import architecture_router
from .deployment import deployment_router
from .development import development_router
from .requirements import requirements_router
from .testing import testing_router

__all__ = [
    "requirements_router",
    "architecture_router",
    "development_router",
    "testing_router",
    "deployment_router",
]
