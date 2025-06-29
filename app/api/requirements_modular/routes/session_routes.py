"""
会话管理路由模块

提供会话管理相关的API路由
"""

from typing import Dict

from fastapi import APIRouter, HTTPException

from ..handlers.session_handler import SessionHandler

# 创建路由器
session_router = APIRouter(prefix="/session", tags=["Session"])

# 创建处理程序实例
session_handler = SessionHandler()


@session_router.get("/{session_id}")
async def get_session(session_id: str) -> Dict:
    """获取会话信息"""
    result = await session_handler.get_session(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@session_router.get("/active/list")
async def get_active_sessions() -> Dict:
    """获取活跃会话列表"""
    result = await session_handler.get_active_sessions()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@session_router.get("/{session_id}/progress")
async def get_session_progress(session_id: str) -> Dict:
    """获取会话进度"""
    result = await session_handler.get_progress(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
