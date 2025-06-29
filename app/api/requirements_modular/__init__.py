"""
模块化需求分析API
"""

from fastapi import APIRouter

from .middleware.logging import LoggingMiddleware
from .routes.analysis_routes import analysis_router
from .routes.clarification_routes import clarification_router
from .routes.session_routes import session_router
from .routes.workflow_routes import router as workflow_router

# 创建主路由器 - 不添加/api前缀，因为已经在主路由中添加了
requirements_router = APIRouter(prefix="/requirements", tags=["Requirements"])

# 注册子路由
requirements_router.include_router(workflow_router)
requirements_router.include_router(analysis_router)
requirements_router.include_router(clarification_router)
requirements_router.include_router(session_router)

# 导出路由器
__all__ = ["requirements_router"]
