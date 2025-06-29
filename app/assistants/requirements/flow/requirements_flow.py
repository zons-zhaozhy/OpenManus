"""
需求分析主流程
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from app.assistants.requirements.agents.business_analyst.agent import (
    BusinessAnalystAgent,
)
from app.assistants.requirements.agents.requirement_clarifier.agent import (
    RequirementClarifierAgent,
)
from app.code_analysis.code_analysis.analyzer import CodeAnalyzer
from app.core.types import AgentState
from app.knowledge_base.adapters import RequirementsKnowledgeBase
from app.logger import logger

from .core.base import BaseFlow


class RequirementsFlow(BaseFlow):
    """需求分析流程"""

    def __init__(self, session_id: Optional[str] = None) -> None:
        """
        初始化需求分析流程

        Args:
            session_id: 会话ID，如果为None则自动生成
        """
        super().__init__(session_id)
        logger.info(f"初始化RequirementsFlow，会话ID: {self.session_id}")
        self.enable_parallel = True
        # 确保协作管理器初始化后立即初始化智能体
        self._initialize_agents()
        logger.info(
            f"智能体初始化完成，注册的智能体: {self.collaboration_manager.get_all_agents().keys()}"
        )
        self.knowledge_base = RequirementsKnowledgeBase()
        self.code_analyzer = CodeAnalyzer()
        self.state = {
            "requirement_text": "",
            "clarification_result": {},
            "analysis_result": {},
            "document_result": {},
            "review_result": {},
            "final_result": {},
        }

    def _initialize_agents(self) -> None:
        """初始化智能体"""
        logger.info("初始化智能体...")

        # 创建智能体实例 (传递当前flow引用)
        self.clarifier = RequirementClarifierAgent(flow=self)
        self.analyzer = BusinessAnalystAgent(flow=self)

        # 注册智能体
        self.collaboration_manager.register_agent("clarifier", self.clarifier)
        self.collaboration_manager.register_agent("analyzer", self.analyzer)

        # 初始化智能体状态
        for agent_id in ["clarifier", "analyzer"]:
            self.collaboration_manager.update_state(
                agent_id, state=AgentState.INITIALIZING.value
            )

    async def process(self, input_text: str) -> Dict[str, Any]:
        """
        处理输入

        Args:
            input_text: 输入文本

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            logger.info(f"开始处理需求: {input_text[:50]}...")
            self.state["requirement_text"] = input_text

            # 1. 获取知识库上下文
            logger.info("步骤1: 获取知识库上下文")
            try:
                knowledge = await asyncio.wait_for(
                    self._get_knowledge_context(input_text), timeout=30
                )
                logger.info(
                    f"✅ 知识库上下文获取成功，找到 {len(knowledge.get('results', []))} 条相关记录"
                )
            except asyncio.TimeoutError:
                logger.error("❌ 获取知识库上下文超时")
                knowledge = {"results": [], "error": "获取知识库上下文超时"}
            except Exception as e:
                logger.error(f"❌ 获取知识库上下文失败: {str(e)}")
                knowledge = {"results": [], "error": str(e)}

            # 2. 获取代码分析结果
            logger.info("步骤2: 获取代码分析结果")
            try:
                code_analysis = await asyncio.wait_for(
                    self._get_code_analysis(input_text), timeout=30
                )
                logger.info(
                    f"✅ 代码分析完成，找到 {len(code_analysis.get('components', []))} 个相关组件"
                )
            except asyncio.TimeoutError:
                logger.error("❌ 代码分析超时")
                code_analysis = {"components": [], "error": "代码分析超时"}
            except Exception as e:
                logger.error(f"❌ 代码分析失败: {str(e)}")
                code_analysis = {"components": [], "error": str(e)}

            # 3. 需求澄清
            logger.info("步骤3: 需求澄清")
            try:
                clarifier = self.collaboration_manager.get_agent("clarifier")
                logger.info("获取到需求澄清智能体")

                clarification_result = await asyncio.wait_for(
                    clarifier.clarify_requirements(
                        input_text, knowledge, code_analysis
                    ),
                    timeout=60,
                )
                logger.info("✅ 需求澄清完成")
                self.state["clarification_result"] = clarification_result
            except asyncio.TimeoutError:
                logger.error("❌ 需求澄清超时")
                self.state["clarification_result"] = {
                    "error": "需求澄清超时",
                    "status": "error",
                }
            except Exception as e:
                logger.error(f"❌ 需求澄清失败: {str(e)}")
                self.state["clarification_result"] = {
                    "error": str(e),
                    "status": "error",
                }

            # 4. 业务分析
            logger.info("步骤4: 业务分析")
            try:
                analyzer = self.collaboration_manager.get_agent("analyzer")
                logger.info("获取到业务分析智能体")

                analysis_result = await asyncio.wait_for(
                    analyzer.analyze_business(
                        input_text,
                        self.state["clarification_result"],
                        knowledge,
                        code_analysis,
                    ),
                    timeout=60,
                )
                logger.info("✅ 业务分析完成")
                self.state["analysis_result"] = analysis_result
            except asyncio.TimeoutError:
                logger.error("❌ 业务分析超时")
                self.state["analysis_result"] = {
                    "error": "业务分析超时",
                    "status": "error",
                }
            except Exception as e:
                logger.error(f"❌ 业务分析失败: {str(e)}")
                self.state["analysis_result"] = {"error": str(e), "status": "error"}

            # 5. 文档生成
            logger.info("步骤5: 文档生成")
            try:
                writer = self._get_technical_writer_agent()
                logger.info("获取到技术文档编写智能体")

                document_result = await asyncio.wait_for(
                    writer.generate_document(
                        input_text,
                        self.state["clarification_result"],
                        self.state["analysis_result"],
                    ),
                    timeout=60,
                )
                logger.info("✅ 文档生成完成")
                self.state["document_result"] = document_result
            except asyncio.TimeoutError:
                logger.error("❌ 文档生成超时")
                self.state["document_result"] = {
                    "error": "文档生成超时",
                    "status": "error",
                }
            except Exception as e:
                logger.error(f"❌ 文档生成失败: {str(e)}")
                self.state["document_result"] = {"error": str(e), "status": "error"}

            # 6. 质量评审
            logger.info("步骤6: 质量评审")
            try:
                reviewer = self._get_quality_reviewer_agent()
                logger.info("获取到质量评审智能体")

                review_result = await asyncio.wait_for(
                    reviewer.review_requirements(
                        input_text,
                        self.state["clarification_result"],
                        self.state["analysis_result"],
                        self.state["document_result"],
                    ),
                    timeout=60,
                )
                logger.info("✅ 质量评审完成")
                self.state["review_result"] = review_result
            except asyncio.TimeoutError:
                logger.error("❌ 质量评审超时")
                self.state["review_result"] = {
                    "error": "质量评审超时",
                    "status": "error",
                }
            except Exception as e:
                logger.error(f"❌ 质量评审失败: {str(e)}")
                self.state["review_result"] = {"error": str(e), "status": "error"}

            # 7. 整合最终结果
            logger.info("步骤7: 整合最终结果")
            self.state["final_result"] = self._integrate_results()
            logger.info("✅ 需求分析完成")

            return self.state
        except Exception as e:
            logger.error(f"需求分析过程中出现错误: {str(e)}")
            self.state["error"] = str(e)
            return self.state

    async def _get_knowledge_context(self, requirement_text: str) -> Dict[str, Any]:
        """获取与需求相关的知识库上下文"""
        logger.debug(f"查询知识库: {requirement_text[:30]}...")
        try:
            results = await self.knowledge_base.query(requirement_text, top_k=3)
            logger.debug(f"知识库查询结果: {len(results.get('results', []))} 条记录")
            return {"results": results.get("results", [])}
        except Exception as e:
            logger.error(f"知识库查询失败: {str(e)}")
            return {"results": [], "error": str(e)}

    async def _get_code_analysis(self, requirement_text: str) -> Dict[str, Any]:
        """获取与需求相关的代码分析结果"""
        logger.debug(f"分析代码库: {requirement_text[:30]}...")
        try:
            components = await self.code_analyzer.analyze_for_requirement(
                requirement_text
            )
            logger.debug(f"代码分析结果: {len(components)} 个组件")
            return {"components": components}
        except Exception as e:
            logger.error(f"代码分析失败: {str(e)}")
            return {"components": [], "error": str(e)}

    def _get_technical_writer_agent(self) -> RequirementClarifierAgent:
        """获取技术文档编写智能体实例"""
        logger.debug("创建技术文档编写智能体...")
        return RequirementClarifierAgent(self)

    def _get_quality_reviewer_agent(self) -> RequirementClarifierAgent:
        """获取质量评审智能体实例"""
        logger.debug("创建质量评审智能体...")
        return RequirementClarifierAgent(self)

    def _integrate_results(self) -> Dict[str, Any]:
        """整合所有分析结果，生成最终输出"""
        logger.debug("整合分析结果...")

        # 检查是否有任何步骤失败
        errors = {}
        for key, value in self.state.items():
            if isinstance(value, dict) and "error" in value:
                errors[key] = value["error"]

        if errors:
            logger.warning(f"分析过程中存在错误: {errors}")

        # 整合结果
        final_result = {
            "timestamp": datetime.now().isoformat(),
            "requirement_text": self.state["requirement_text"],
            "clarification": self._extract_clarification_summary(),
            "analysis": self._extract_analysis_summary(),
            "document": self._extract_document_summary(),
            "review": self._extract_review_summary(),
            "status": (
                "success"
                if not errors
                else "partial_success" if len(errors) < 3 else "failed"
            ),
            "errors": errors,
        }

        logger.debug(f"最终结果状态: {final_result['status']}")
        return final_result

    def _extract_clarification_summary(self) -> Dict[str, Any]:
        """提取需求澄清结果摘要"""
        result = self.state.get("clarification_result", {})
        if not result or "error" in result:
            return {"status": "failed"}

        return {
            "status": "success",
            "questions_count": len(result.get("questions", [])),
            "clarification_needed": result.get("clarification_needed", True),
            "summary": result.get("summary", ""),
        }

    def _extract_analysis_summary(self) -> Dict[str, Any]:
        """提取业务分析结果摘要"""
        result = self.state.get("analysis_result", {})
        if not result or "error" in result:
            return {"status": "failed"}

        return {
            "status": "success",
            "key_points": result.get("key_points", []),
            "business_value": result.get("business_value", ""),
            "summary": result.get("summary", ""),
        }

    def _extract_document_summary(self) -> Dict[str, Any]:
        """提取文档生成结果摘要"""
        result = self.state.get("document_result", {})
        if not result or "error" in result:
            return {"status": "failed"}

        return {
            "status": "success",
            "document_type": result.get("document_type", ""),
            "sections_count": len(result.get("sections", [])),
            "summary": result.get("summary", ""),
        }

    def _extract_review_summary(self) -> Dict[str, Any]:
        """提取质量评审结果摘要"""
        result = self.state.get("review_result", {})
        if not result or "error" in result:
            return {"status": "failed"}

        return {
            "status": "success",
            "quality_score": result.get("quality_score", 0),
            "issues_count": len(result.get("issues", [])),
            "summary": result.get("summary", ""),
        }
