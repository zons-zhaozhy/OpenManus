"""
部署安装助手API路由
"""

from fastapi import APIRouter

deployment_router = APIRouter(prefix="/api/deployment", tags=["Deployment"])


@deployment_router.get("/")
async def get_deployment_info():
    """获取部署安装助手信息"""
    return {
        "name": "部署安装助手",
        "status": "framework_ready",
        "description": "智能化部署安装助手",
    }


@deployment_router.post("/deploy")
async def deploy_system():
    """部署系统"""
    return {"message": "系统部署功能开发中", "status": "coming_soon"}
