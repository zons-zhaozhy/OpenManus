"""
需求澄清处理器
"""

from typing import Any, Dict, List, Optional

from app.assistants.requirements.flow import RequirementsFlow
from app.logger import logger


class ClarificationHandler:
    """需求澄清处理器"""

    def __init__(self):
        self.flow = RequirementsFlow()

    async def generate_question(
        self, requirement: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成澄清问题

        Args:
            requirement: 需求内容
            context: 上下文信息

        Returns:
            Dict[str, Any]: 澄清问题
        """
        try:
            result = await self.flow.generate_clarification_question(
                requirement, context
            )
            return result
        except Exception as e:
            logger.error(f"生成澄清问题失败: {e}")
            raise

    async def process_answer(
        self, question: str, answer: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理澄清答案

        Args:
            question: 澄清问题
            answer: 用户答案
            context: 上下文信息

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            result = await self.flow.process_clarification_answer(
                question, answer, context
            )
            return result
        except Exception as e:
            logger.error(f"处理澄清答案失败: {e}")
            raise
