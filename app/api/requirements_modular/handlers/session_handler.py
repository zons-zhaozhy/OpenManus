"""
会话管理处理程序
"""

from typing import Dict

from app.logger import logger

from ..storage import session_storage


class SessionHandler:
    """会话管理处理程序"""

    async def get_session(self, session_id: str) -> Dict:
        """获取会话信息"""
        try:
            session_data = session_storage.get_session(session_id)
            if not session_data:
                raise ValueError(f"无效的会话ID: {session_id}")
            return session_data
        except Exception as e:
            logger.error(f"获取会话失败: {str(e)}")
            return {"error": f"获取失败: {str(e)}"}

    async def get_active_sessions(self) -> Dict:
        """获取活跃会话列表"""
        try:
            active_sessions = session_storage.get_active_sessions()
            return {"active_sessions": list(active_sessions.keys())}
        except Exception as e:
            logger.error(f"获取活跃会话失败: {str(e)}")
            return {"error": f"获取失败: {str(e)}"}

    async def get_progress(self, session_id: str) -> Dict:
        """获取会话进度"""
        try:
            progress = session_storage.get_session_progress(session_id)
            return progress
        except Exception as e:
            logger.error(f"获取进度失败: {str(e)}")
            return {"error": f"获取失败: {str(e)}"}
