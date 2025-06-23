"""
系统测试助手API路由
"""

from fastapi import APIRouter

testing_router = APIRouter(prefix="/api/testing", tags=["Testing"])


@testing_router.get("/")
async def get_testing_info():
    """获取系统测试助手信息"""
    return {
        "name": "系统测试助手",
        "status": "framework_ready",
        "description": "智能化系统测试助手",
    }


@testing_router.post("/test")
async def run_tests():
    """运行测试"""
    return {"message": "系统测试功能开发中", "status": "coming_soon"}
