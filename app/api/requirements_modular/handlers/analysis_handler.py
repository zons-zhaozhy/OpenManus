"""
需求分析处理器
"""

from typing import Any, Dict, List, Optional

from app.assistants.requirements.flow import RequirementsFlow
from app.logger import logger


class AnalysisHandler:
    """需求分析处理器"""

    def __init__(self):
        self.flow = RequirementsFlow()

    async def analyze_requirements(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析需求

        Args:
            content: 需求内容
            context: 上下文信息

        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 执行需求分析流程
            result = await self.flow.execute(content)

            # 构造标准响应格式
            response = {
                "session_id": self.flow.session_id,
                "status": (
                    result.get("status", "success")
                    if isinstance(result, dict)
                    else "success"
                ),
                "message": (
                    result.get("message", "需求分析完成")
                    if isinstance(result, dict)
                    else "需求分析完成"
                ),
                "result": result,
            }

            return response
        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            # 构造错误响应
            return {
                "session_id": getattr(self.flow, "session_id", "unknown"),
                "status": "error",
                "message": f"需求分析失败: {str(e)}",
                "result": None,
            }

    async def get_analysis_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取分析状态

        Args:
            session_id: 会话ID

        Returns:
            Dict[str, Any]: 分析状态
        """
        try:
            # 获取流程进度
            if (
                hasattr(self.flow, "get_progress")
                and self.flow.session_id == session_id
            ):
                progress = self.flow.get_progress()
                return {
                    "session_id": session_id,
                    "status": (
                        "in_progress"
                        if progress.get("percentage", 100) < 100
                        else "completed"
                    ),
                    "progress": progress,
                }

            # 默认返回
            return {
                "session_id": session_id,
                "status": "completed",
                "progress": 100,
            }
        except Exception as e:
            logger.error(f"获取分析状态失败: {e}")
            raise
