"""
需求分析路由模块

提供所有API路由的注册和管理
"""

from fastapi import APIRouter

from .analysis_routes import analysis_router
from .clarification_routes import clarification_router
from .session_routes import session_router
from .workflow_routes import router as workflow_router

# 创建主路由器
requirements_router = APIRouter(prefix="/api/requirements", tags=["Requirements"])

# 注册子路由
requirements_router.include_router(analysis_router)
requirements_router.include_router(clarification_router)
requirements_router.include_router(session_router)
requirements_router.include_router(workflow_router)

__all__ = ["requirements_router"]
