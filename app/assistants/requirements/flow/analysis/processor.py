"""
需求分析流程的分析处理模块
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.code_analysis import CodeAnalyzer
from app.core.types import AgentState
from app.knowledge_base import VectorKnowledgeBase
from app.logger import logger

from ..core.base import BaseRequirementsFlow


class RequirementsAnalysisProcessor:
    """需求分析处理器"""

    def __init__(self, flow: BaseRequirementsFlow):
        self.flow = flow
        self.context_manager = flow.context_manager
        self.knowledge_base = VectorKnowledgeBase()
        self.code_analyzer = CodeAnalyzer()

    async def _clarify_requirements_enhanced(self, user_input: str) -> str:
        """增强的需求澄清流程"""
        logger.info("开始需求澄清流程")

        clarifier = self.flow.agents["clarifier"]
        try:
            await self.flow.collaboration_manager.update_state(
                clarifier.id, state=AgentState.WORKING, task="需求澄清"
            )
        except Exception as e:
            logger.warning(f"状态更新失败（非致命）: {str(e)}")

        # 使用知识库和代码分析结果增强澄清过程
        clarification_result = await clarifier.clarify_requirements(
            user_input,
            self.flow.knowledge_base.get_relevant_knowledge(),
            self.flow.code_analyzer.get_analysis_results(),
        )

        await self.flow.collaboration_manager.update_state(
            clarifier.id, AgentState.COMPLETED, task="需求澄清完成"
        )

        self.flow.clarification_complete = True
        return clarification_result

    async def _analyze_business_enhanced(self, clarification_result: str) -> str:
        """增强的业务分析流程"""
        logger.info("开始业务分析流程")

        analyst = self.flow.agents["analyst"]
        await self.flow.collaboration_manager.update_state(
            analyst.id, AgentState.WORKING, task="业务分析"
        )

        # 使用知识库和代码分析结果增强分析过程
        analysis_result = await analyst.analyze_business(
            clarification_result,
            self.flow.knowledge_base.get_relevant_knowledge(),
            self.flow.code_analyzer.get_analysis_results(),
        )

        await self.flow.collaboration_manager.update_state(
            analyst.id, AgentState.COMPLETED, task="业务分析完成"
        )

        self.flow.analysis_complete = True
        return analysis_result

    async def _write_documentation_enhanced(self, analysis_result: str) -> str:
        """增强的文档编写流程"""
        logger.info("开始文档编写流程")

        writer = self.flow.agents["writer"]
        await self.flow.collaboration_manager.update_state(
            writer.id, AgentState.WORKING, task="文档编写"
        )

        # 使用知识库增强文档编写过程
        documentation_result = await writer.write_documentation(
            analysis_result, self.flow.knowledge_base.get_relevant_knowledge()
        )

        await self.flow.collaboration_manager.update_state(
            writer.id, AgentState.COMPLETED, task="文档编写完成"
        )

        return documentation_result

    async def _parallel_preprocessing(self, user_input: str):
        """并行预处理"""
        logger.info("开始并行预处理")

        try:
            # 并行执行知识库和代码分析预处理
            tasks = [
                self._preprocess_with_knowledge_base(user_input),
                self._preprocess_with_code_analysis(user_input),
            ]
            # 使用 return_exceptions=True 确保即使有任务失败也不会中断
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 检查结果中是否有异常
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_name = "知识库预处理" if i == 0 else "代码分析预处理"
                    logger.warning(f"{task_name}失败（非致命）: {str(result)}")
        except Exception as e:
            logger.warning(f"预处理过程中发生错误（非致命）: {str(e)}")
            # 继续执行，不中断流程

    async def _parallel_analysis_flow(self) -> str:
        """并行分析流程"""
        logger.info("开始并行分析流程")

        # 获取用户输入
        user_input = self.flow.state_manager.get_data("user_input")

        # 并行执行需求澄清和业务分析
        clarification_result, analysis_result = await asyncio.gather(
            self._clarify_requirements_enhanced(user_input),
            self._analyze_business_enhanced(user_input),
        )

        # 串行执行文档编写和质量评审
        documentation_result = await self._write_documentation_enhanced(analysis_result)

        return documentation_result

    async def _sequential_analysis_flow(self) -> str:
        """顺序分析流程"""
        logger.info("开始顺序分析流程")

        # 获取用户输入
        user_input = self.flow.state_manager.get_data("user_input")

        # 顺序执行各个步骤
        clarification_result = await self._clarify_requirements_enhanced(user_input)
        analysis_result = await self._analyze_business_enhanced(clarification_result)
        documentation_result = await self._write_documentation_enhanced(analysis_result)

        return documentation_result

    async def _query_knowledge_base(self, user_input: str) -> Dict[str, Any]:
        """查询知识库"""
        try:
            results = await self.knowledge_base.search(user_input)
            return {
                "matches": results.get("matches", []),
                "total_found": results.get("total", 0),
                "query_time": results.get("query_time_ms", 0),
            }
        except Exception as e:
            logger.error(f"知识库查询失败: {str(e)}")
            return {"matches": [], "total_found": 0, "query_time": 0}

    async def _analyze_code(self, user_input: str) -> Dict[str, Any]:
        """代码分析"""
        try:
            # 直接调用同步方法，因为代码分析本身就是CPU密集型操作
            results = self.code_analyzer.analyze_codebase(
                codebase_id="temp",
                root_path=self.flow.project_root or ".",
            )

            # 转换结果格式
            return {
                "patterns": [
                    p.dict() for p in results.components if hasattr(p, "dict")
                ],
                "metrics": {
                    "total_files": results.file_count,
                    "total_lines": results.total_lines,
                    "languages": results.languages,
                    "complexity": results.metrics.cyclomatic_complexity,
                    "maintainability": results.metrics.maintainability_index,
                },
                "suggestions": results.suggestions,
            }
        except Exception as e:
            logger.error(f"代码分析失败: {str(e)}")
            return {"patterns": [], "metrics": {}, "suggestions": []}

    async def _preprocess_with_knowledge_base(self, user_input: str) -> Dict[str, Any]:
        """知识库预处理"""
        try:
            results = await self._query_knowledge_base(user_input)
            self.context_manager.update_global_state("knowledge_base_results", results)
            return results
        except Exception as e:
            logger.error(f"知识库预处理失败: {str(e)}")
            return {"error": str(e), "matches": [], "total_found": 0}

    async def _preprocess_with_code_analysis(self, user_input: str) -> Dict[str, Any]:
        """代码分析预处理"""
        try:
            results = await self._analyze_code(user_input)
            self.context_manager.update_global_state("code_analysis_results", results)
            return results
        except Exception as e:
            logger.error(f"代码分析预处理失败: {str(e)}")
            return {"error": str(e), "patterns": [], "metrics": {}, "suggestions": []}

    async def process_requirements(self, user_input: str) -> Dict[str, Any]:
        """处理需求分析"""
        try:
            # 并行执行知识库和代码分析
            kb_task = self._process_knowledge_base(user_input)
            code_task = self._process_code_analysis(user_input)

            results = await asyncio.gather(kb_task, code_task)
            kb_results, code_results = results

            # 更新上下文
            self.context_manager.update_global_state(
                {
                    "knowledge_base_results": kb_results,
                    "code_analysis_results": code_results,
                    "last_processed": datetime.now().isoformat(),
                }
            )

            return {"knowledge_base": kb_results, "code_analysis": code_results}

        except Exception as e:
            logger.error(f"需求处理失败: {str(e)}")
            raise

    async def _process_knowledge_base(self, user_input: str) -> Dict[str, Any]:
        """处理知识库查询"""
        try:
            results = await self.knowledge_base.search(user_input)
            processed_results = {
                "matches": results.get("matches", []),
                "total_found": results.get("total", 0),
                "query_time": results.get("query_time", 0),
                "processed_at": datetime.now().isoformat(),
            }
            return processed_results
        except Exception as e:
            logger.error(f"知识库处理失败: {str(e)}")
            return {"error": str(e), "matches": [], "total_found": 0}

    async def _process_code_analysis(self, user_input: str) -> Dict[str, Any]:
        """处理代码分析"""
        try:
            results = await self._analyze_code(user_input)
            processed_results = {
                "findings": results.get("findings", []),
                "metrics": results.get("metrics", {}),
                "suggestions": results.get("suggestions", []),
                "processed_at": datetime.now().isoformat(),
            }
            return processed_results
        except Exception as e:
            logger.error(f"代码分析失败: {str(e)}")
            return {"error": str(e), "findings": [], "metrics": {}}
