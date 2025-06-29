"""
基础流程类
"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.assistants.requirements.collaboration_manager import CollaborationManager
from app.assistants.requirements.flow.core.state_manager import StateManager
from app.code_analysis import CodeAnalyzer
from app.knowledge_base import VectorKnowledgeBase as KnowledgeBase
from app.logger import logger


class BaseFlow:
    """基础流程类"""

    def __init__(self, session_id: Optional[str] = None) -> None:
        """
        初始化基础流程

        Args:
            session_id: 会话ID，如果为None则自动生成
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.state_manager = StateManager()
        self.collaboration_manager = CollaborationManager()
        self.knowledge_base = KnowledgeBase()
        self.code_analyzer = CodeAnalyzer()
        self.context: Dict[str, Any] = {}
        self._initialize_context()
        self._initialize_flow()

    def _initialize_context(self) -> None:
        """初始化上下文"""
        self.context = {
            "session_id": self.session_id,
            "state": self.state_manager.current_state,
            "knowledge": {},
            "code_analysis": {},
            "agents": {},
            "messages": [],
            "results": {},
        }

    def _initialize_flow(self) -> None:
        """初始化流程，子类可以重写此方法"""
        # 设置初始状态
        try:
            self.state_manager.set_state("READY")
            logger.info(f"流程 {self.__class__.__name__} 初始化完成，状态: READY")
        except Exception as e:
            logger.error(f"初始化流程状态失败: {str(e)}")
            raise ValueError(f"初始化流程状态失败: {str(e)}")

    async def _preprocess_with_knowledge_base(self, input_text: str) -> Dict[str, Any]:
        """
        使用知识库预处理输入

        Args:
            input_text: 输入文本

        Returns:
            Dict[str, Any]: 知识库处理结果
        """
        try:
            logger.info("开始使用知识库预处理输入...")
            knowledge_results = await self.knowledge_base.query(input_text)
            logger.info(f"知识库预处理完成，获取到 {len(knowledge_results)} 条相关知识")
            return knowledge_results
        except Exception as e:
            logger.error(f"知识库预处理失败: {str(e)}")
            # 返回空结果而不是抛出异常
            return {"error": str(e), "results": []}

    async def _preprocess_with_code_analysis(self, input_text: str) -> Dict[str, Any]:
        """
        使用代码分析预处理输入

        Args:
            input_text: 输入文本

        Returns:
            Dict[str, Any]: 代码分析结果
        """
        try:
            logger.info("开始使用代码分析预处理输入...")
            code_analysis_results = await self.code_analyzer.analyze(input_text)
            logger.info("代码分析预处理完成")
            return code_analysis_results
        except Exception as e:
            logger.error(f"代码分析预处理失败: {str(e)}")
            # 返回空结果而不是抛出异常
            return {"error": str(e), "results": []}

    async def preprocess(self, input_text: str) -> Dict[str, Any]:
        """
        预处理输入

        Args:
            input_text: 输入文本

        Returns:
            Dict[str, Any]: 预处理结果
        """
        try:
            logger.info(f"开始预处理输入: {input_text[:50]}...")

            # 并行执行知识库和代码分析预处理
            knowledge_task = asyncio.create_task(
                self._preprocess_with_knowledge_base(input_text)
            )
            code_analysis_task = asyncio.create_task(
                self._preprocess_with_code_analysis(input_text)
            )

            # 等待所有预处理任务完成
            knowledge_results, code_analysis_results = await asyncio.gather(
                knowledge_task, code_analysis_task
            )

            # 更新上下文
            self.context["knowledge"] = knowledge_results
            self.context["code_analysis"] = code_analysis_results

            logger.info("预处理完成")

            return {
                "knowledge": knowledge_results,
                "code_analysis": code_analysis_results,
            }
        except Exception as e:
            logger.error(f"预处理失败: {str(e)}")
            # 返回错误信息而不是抛出异常
            return {
                "error": str(e),
                "knowledge": {},
                "code_analysis": {},
            }

    async def process(self, input_text: str) -> Dict[str, Any]:
        """
        处理输入

        Args:
            input_text: 输入文本

        Returns:
            Dict[str, Any]: 处理结果
        """
        raise NotImplementedError("子类必须实现process方法")

    async def postprocess(self, process_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        后处理结果

        Args:
            process_results: 处理结果

        Returns:
            Dict[str, Any]: 后处理结果
        """
        try:
            logger.info("开始后处理结果...")

            # 更新上下文
            self.context["results"] = process_results

            # 可以在这里添加后处理逻辑

            logger.info("后处理完成")

            return process_results
        except Exception as e:
            logger.error(f"后处理失败: {str(e)}")
            raise

    async def execute(self, input_text: str) -> Dict[str, Any]:
        """
        执行流程

        Args:
            input_text: 输入文本

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 检查状态
            if self.state_manager.current_state != "READY":
                error_msg = f"Flow must be in READY state before execution, current state: {self.state_manager.current_state}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 更新状态为处理中
            logger.info("开始执行流程...")
            self.state_manager.set_state("PROCESSING")

            # 预处理
            logger.info("执行预处理...")
            preprocess_results = await self.preprocess(input_text)

            # 处理
            logger.info("执行处理...")
            process_results = await self.process(input_text)

            # 后处理
            logger.info("执行后处理...")
            final_results = await self.postprocess(process_results)

            # 更新状态为完成
            logger.info("流程执行完成")
            self.state_manager.set_state("COMPLETED")

            return final_results
        except Exception as e:
            logger.error(f"流程执行失败: {str(e)}")

            # 特殊处理READY错误
            if str(e) == "READY" or "READY" in str(e):
                logger.info("捕获到READY错误，不更新状态")
                # 直接重新抛出，让上层处理
                raise ValueError("READY")

            # 更新状态为错误
            self.state_manager.set_state("ERROR", error=str(e))

            # 重新抛出异常
            raise
