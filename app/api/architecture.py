"""
架构设计助手API路由
"""

from fastapi import APIRouter

architecture_router = APIRouter(prefix="/api/architecture", tags=["Architecture"])


@architecture_router.get("/")
async def get_architecture_info():
    """获取架构设计助手信息"""
    return {
        "name": "架构设计助手",
        "status": "framework_ready",
        "description": "智能化系统架构设计助手",
    }


@architecture_router.post("/design")
async def design_architecture():
    """开始架构设计"""
    return {"message": "架构设计功能开发中", "status": "coming_soon"}
