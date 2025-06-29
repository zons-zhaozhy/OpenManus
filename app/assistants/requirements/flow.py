"""
需求分析助手流程 - 基于BaseFlow的多智能体协作

充分利用OpenManus现有能力：
- 继承BaseFlow进行多智能体管理
- 所有智能体继承BaseAgent，自动获得LLM、内存、状态管理
- 使用现有的配置系统和提示词系统
- 集成知识库和代码分析能力
- 优化的上下文共享机制
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import ConfigDict, Field

from app.agent.base import BaseAgent
from app.assistants.requirements.flow.core.state_manager import StateManager
from app.code_analysis import CodeAnalyzer
from app.core.types import AgentState
from app.flow.base import BaseFlow
from app.flow.mixins import (
    BaseMixin,
    ErrorHandlingMixin,
    ErrorSeverity,
    ProjectManagementMixin,
)
from app.flow.state import FlowState
from app.knowledge_base.adapters import RequirementsKnowledgeBase
from app.llm import LLM
from app.logger import log_exception, logger
from app.modules.knowledge_base.core.knowledge_manager import KnowledgeCategory
from app.schema import Message

from .agents.business_analyst import BusinessAnalystAgent
from .agents.quality_reviewer import QualityReviewerAgent
from .agents.requirement_clarifier import RequirementClarifierAgent
from .agents.technical_writer import TechnicalWriterAgent
from .collaboration_manager import CollaborationManager
from .context_manager import RequirementsContextManager


class RequirementsFlow(BaseFlow, ProjectManagementMixin, ErrorHandlingMixin):
    """需求分析流程"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # 正确定义Pydantic字段
    current_context: Dict[str, Any] = Field(default_factory=dict)
    clarification_complete: bool = Field(default=False)
    analysis_complete: bool = Field(default=False)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_manager: Optional[RequirementsContextManager] = Field(default=None)
    knowledge_base: Optional[RequirementsKnowledgeBase] = Field(default=None)
    code_analyzer: Optional[CodeAnalyzer] = Field(default=None)
    collaboration_manager: Optional[CollaborationManager] = Field(default=None)
    enable_parallel: bool = Field(default=True)
    progress_callback: Optional[Callable] = Field(default=None)
    project_root: str = Field(default=os.getcwd())

    def __init__(self, project_id: Optional[str] = None, **kwargs):
        try:
            logger.info("开始初始化 RequirementsFlow")

            # 设置项目根目录
            self.project_root = kwargs.get("project_root", os.getcwd())
            logger.info(f"项目根目录: {self.project_root}")

            # 创建专门的智能体团队（包含质量保证）
            logger.info("创建智能体团队")
            try:
                agents = {
                    "clarifier": RequirementClarifierAgent(
                        name="需求澄清师", description="负责澄清模糊的用户需求"
                    ),
                    "analyst": BusinessAnalystAgent(
                        name="业务分析师", description="负责深度业务分析"
                    ),
                    "writer": TechnicalWriterAgent(
                        name="技术文档编写师", description="负责编写需求规格说明书"
                    ),
                    "reviewer": QualityReviewerAgent(
                        name="质量审查师", description="负责需求质量审查"
                    ),
                }
                logger.info("智能体团队创建完成")
            except Exception as e:
                logger.error(f"创建智能体团队失败: {str(e)}")
                raise

            # 初始化代码分析器
            try:
                logger.info("初始化代码分析器")
                self.code_analyzer = CodeAnalyzer()
                logger.info("代码分析器初始化完成")
            except Exception as e:
                logger.error(f"初始化代码分析器失败: {str(e)}")
                raise

            # 初始化知识库
            try:
                logger.info("初始化知识库")
                self.knowledge_base = RequirementsKnowledgeBase()
                logger.info("知识库初始化完成")
            except Exception as e:
                logger.error(f"初始化知识库失败: {str(e)}")
                raise

            # 初始化上下文管理器
            try:
                logger.info("初始化上下文管理器")
                self.context_manager = RequirementsContextManager(self.session_id)
                logger.info("上下文管理器初始化完成")
            except Exception as e:
                logger.error(f"初始化上下文管理器失败: {str(e)}")
                raise

            # 初始化协作管理器
            try:
                logger.info("初始化协作管理器")
                self.collaboration_manager = CollaborationManager(agents)
                logger.info("协作管理器初始化完成")
            except Exception as e:
                logger.error(f"初始化协作管理器失败: {str(e)}")
                raise

            # 初始化状态管理器
            try:
                logger.info("初始化状态管理器")
                self.state_manager = StateManager()
                logger.info("状态管理器初始化完成")
            except Exception as e:
                logger.error(f"初始化状态管理器失败: {str(e)}")
                raise

            # 设置会话ID
            self.session_id = str(uuid.uuid4())
            logger.info(f"会话ID: {self.session_id}")

            # 设置状态
            self.status = "READY"
            self.clarification_complete = False
            self.analysis_complete = False
            self.documentation_complete = False
            self.review_complete = False

            logger.info("流程 RequirementsFlow 初始化完成，状态: READY")

        except Exception as e:
            logger.error(f"初始化 RequirementsFlow 失败: {str(e)}")
            raise

    async def verify_agent_registration(self) -> bool:
        """
        验证所有智能体是否已正确注册

        Returns:
            bool: 是否所有智能体都已正确注册
        """
        try:
            all_registered = True
            for agent_key, agent in self.agents.items():
                if agent.id not in self.collaboration_manager._states:
                    logger.error(f"智能体未注册: {agent_key} (ID: {agent.id})")
                    all_registered = False
                    # 尝试重新注册
                    try:
                        self.collaboration_manager.register_agent_sync(agent)
                        logger.info(f"已重新注册智能体: {agent_key}")
                    except Exception as e:
                        logger.error(f"重新注册智能体失败: {agent_key}, 错误: {str(e)}")
            return all_registered
        except Exception as e:
            logger.error(f"验证智能体注册状态失败: {str(e)}")
            return False

    async def execute(self, input_text: str) -> Dict[str, Any]:
        """
        执行需求分析流程

        Args:
            input_text: 用户输入的需求描述

        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            logger.info(f"开始执行需求分析流程，输入: {input_text[:50]}...")

            # 更新全局状态
            self.context_manager.update_global_state("user_input", input_text)
            self.context_manager.update_global_state("current_stage", "初始化")

            # 保存用户输入到当前上下文
            self.current_context["user_input"] = input_text

            # 验证智能体注册状态
            if not await self.verify_agent_registration():
                raise ValueError("智能体注册验证失败")

            # 执行需求分析流程
            try:
                # 预处理
                await self._parallel_preprocessing(input_text)

                # 根据配置选择并行或串行执行
                if self.enable_parallel:
                    result = await self._parallel_analysis_flow()
                else:
                    result = await self._sequential_analysis_flow()

                # 生成最终报告
                final_report = await self._generate_final_report()

                # 返回成功结果
                return {
                    "status": "success",
                    "message": "需求分析完成",
                    "result": {
                        "analysis": result,
                        "report": final_report,
                        "metrics": self._get_quality_metrics(),
                    },
                }

            except Exception as e:
                logger.error(f"执行需求分析流程时发生错误: {str(e)}")
                return {
                    "status": "error",
                    "message": f"需求分析失败: {str(e)}",
                    "result": None,
                }

        except Exception as e:
            logger.error(f"需求分析流程执行失败: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"需求分析失败: {str(e)}",
                "result": None,
            }

    async def _execute_impl(self, input_text: str) -> Dict[str, Any]:
        """
        实现具体的需求分析流程逻辑

        Args:
            input_text: 用户输入的需求描述

        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            if not input_text or not input_text.strip():
                raise ValueError("需求描述不能为空")

            # 更新全局状态
            self.context_manager.update_global_state("user_input", input_text)
            self.context_manager.update_global_state("current_stage", "初始化")

            # 保存用户输入到当前上下文
            self.current_context["user_input"] = input_text

            # 初始化所有智能体的内存和状态
            for agent_name, agent in self.agents.items():
                agent.memory.clear()
                agent.memory.add_message(Message.user_message(input_text))
                await self.collaboration_manager.update_state(
                    agent.id, AgentState.READY, task="初始化"
                )

            # 预处理
            await self._parallel_preprocessing(input_text)
            if self.progress_callback:
                await self.progress_callback(1, 4, "预处理完成")

            # 根据配置选择并行或串行执行
            if self.enable_parallel:
                analysis_result = await self._parallel_analysis_flow()
            else:
                analysis_result = await self._sequential_analysis_flow()

            if self.progress_callback:
                await self.progress_callback(2, 4, "分析完成")

            # 生成最终报告
            final_report = await self._generate_final_report()
            if self.progress_callback:
                await self.progress_callback(3, 4, "报告生成")

            # 更新所有智能体状态为完成
            for agent_name, agent in self.agents.items():
                await self.collaboration_manager.update_state(
                    agent.id, AgentState.COMPLETED, task="完成"
                )

            if self.progress_callback:
                await self.progress_callback(4, 4, "完成")

            # 返回结果
            return {
                "status": "success",
                "message": "需求分析完成",
                "result": {
                    "analysis": analysis_result,
                    "report": final_report,
                    "metrics": self._get_quality_metrics(),
                },
            }

        except Exception as e:
            # 更新所有智能体状态为错误
            for agent_name, agent in self.agents.items():
                try:
                    await self.collaboration_manager.update_state(
                        agent.id, AgentState.ERROR, task="错误"
                    )
                except Exception as update_err:
                    logger.error(f"更新智能体 {agent_name} 状态失败: {update_err}")

            log_exception(logger, "需求分析执行失败", e)
            raise

    async def _clarify_requirements_enhanced(self, user_input: str) -> str:
        """增强的需求澄清（项目制管理 + 知识库增强）"""
        try:
            self.context_manager.update_global_state("current_stage", "需求澄清")
            self.state_manager.update_data("current_stage", "需求澄清")

            clarifier = self.get_agent("clarifier")

            # 构建项目指引
            project_guidance = self._build_project_guidance_prompt()

            # 构建增强的上下文提示
            base_context_prompt = self.context_manager.build_context_prompt(
                "需求澄清师", "需求澄清"
            )

            # 组合项目指引和基础上下文
            enhanced_context_prompt = f"""
{project_guidance}

{base_context_prompt}

## 用户需求输入
{user_input}

**重要提醒：** 澄清过程必须紧密围绕项目目标展开，确保所有澄清问题都服务于项目的整体成功！
"""

            # 更新智能体记忆
            clarifier.update_memory("system", enhanced_context_prompt)

            # 执行澄清步骤
            result = await clarifier.run()

            # 记录上下文
            self.context_manager.add_context_item(
                agent_name="需求澄清师",
                stage="需求澄清",
                content=result,
                content_type="clarification",
                confidence=0.85,
                metadata={"project_guided": bool(self.project_context)},
            )

            self.current_context["clarification"] = result
            self.clarification_complete = True

            logger.info("项目制管理指引的需求澄清阶段完成")
            return result

        except Exception as e:
            if not await self.handle_error_with_retry(
                e, "需求澄清", ErrorSeverity.HIGH, {"stage": "clarification"}
            ):
                logger.error("需求澄清失败且无法重试")
                raise

    async def _analyze_business_enhanced(self, clarification_result: str) -> str:
        """增强的业务分析（项目制管理指引）"""
        try:
            self.context_manager.update_global_state("current_stage", "业务分析")
            self.state_manager.update_data("current_stage", "业务分析")

            analyst = self.get_agent("analyst")

            # 构建项目指引
            project_guidance = self._build_project_guidance_prompt()

            # 构建增强上下文
            base_context_prompt = self.context_manager.build_context_prompt(
                "业务分析师", "业务分析"
            )

            # 组合提示词
            enhanced_context_prompt = f"""
{project_guidance}

{base_context_prompt}

## 澄清结果
{clarification_result}

**重要提醒：** 业务分析必须基于澄清结果，确保分析的深度和广度！
"""

            # 更新智能体记忆
            analyst.update_memory("system", enhanced_context_prompt)

            # 执行分析步骤
            result = await analyst.run()

            # 记录上下文
            self.context_manager.add_context_item(
                agent_name="业务分析师",
                stage="业务分析",
                content=result,
                content_type="business_analysis",
                confidence=0.85,
                metadata={"project_guided": bool(self.project_context)},
            )

            self.current_context["analysis"] = result
            self.analysis_complete = True
            self.context_manager.update_global_state("business_complexity", "中等")

            logger.info("项目制管理指引的业务分析阶段完成")
            return result

        except Exception as e:
            if not await self.handle_error_with_retry(
                e, "业务分析", ErrorSeverity.HIGH, {"stage": "business_analysis"}
            ):
                logger.error("业务分析失败且无法重试")
                raise

    async def _write_documentation_enhanced(self, analysis_result: str) -> str:
        """增强的文档编写（代码复用建议）"""
        try:
            self.context_manager.update_global_state("current_stage", "文档编写")
            self.state_manager.update_data("current_stage", "文档编写")

            writer = self.get_agent("writer")

            # 获取代码复用建议
            code_suggestions = await self.code_analyzer.get_reuse_suggestions(
                analysis_result
            )

            # 构建项目指引
            project_guidance = self._build_project_guidance_prompt()

            # 构建增强上下文
            base_context_prompt = self.context_manager.build_context_prompt(
                "技术文档编写师", "文档编写"
            )

            # 组合提示词
            enhanced_context_prompt = f"""
{project_guidance}

{base_context_prompt}

## 业务分析结果
{analysis_result}

## 代码复用建议
{code_suggestions}

**重要提醒：** 文档编写要结合业务分析结果和代码复用建议，确保技术可行性！
"""

            # 更新智能体记忆
            writer.update_memory("system", enhanced_context_prompt)

            # 执行文档编写
            result = await writer.run()

            # 记录上下文
            self.context_manager.add_context_item(
                agent_name="技术文档编写师",
                stage="文档编写",
                content=result,
                content_type="documentation",
                confidence=0.9,
                metadata={
                    "project_guided": bool(self.project_context),
                    "has_code_suggestions": bool(code_suggestions),
                },
            )

            self.current_context["documentation"] = result

            logger.info("项目制管理指引的文档编写阶段完成")
            return result

        except Exception as e:
            if not await self.handle_error_with_retry(
                e, "文档编写", ErrorSeverity.HIGH, {"stage": "documentation"}
            ):
                logger.error("文档编写失败且无法重试")
                raise

    async def _quality_review_enhanced(self, documentation_result: str) -> str:
        """增强的质量评审（项目制管理指引）"""
        try:
            self.context_manager.update_global_state("current_stage", "质量评审")
            self.state_manager.update_data("current_stage", "质量评审")

            reviewer = self.get_agent("reviewer")

            # 构建项目指引
            project_guidance = self._build_project_guidance_prompt()

            # 构建增强上下文
            base_context_prompt = self.context_manager.build_context_prompt(
                "质量评审师", "质量评审"
            )

            # 获取所有阶段的关键结果
            clarification = self.current_context.get("clarification", "")
            analysis = self.current_context.get("analysis", "")

            enhanced_prompt = f"""{project_guidance}

{base_context_prompt}

## 需求规格说明书
{documentation_result}

## 需求澄清结果
{clarification}

## 业务分析结果
{analysis}

**重要提醒：** 质量评审必须全面审查所有阶段的成果，确保整体质量！
"""

            # 更新智能体记忆
            reviewer.update_memory("system", enhanced_prompt)

            # 执行质量评审
            review_result = await reviewer.run()

            # 记录上下文
            self.context_manager.add_context_item(
                agent_name="质量评审师",
                stage="质量评审",
                content=review_result,
                content_type="quality_review",
                confidence=0.95,
                metadata={"project_guided": bool(self.project_context)},
            )

            self.current_context["review"] = review_result

            # 检查评审结果，决定是否需要改进
            review_summary = reviewer.get_review_summary()

            if review_summary["total_score"] >= 70:
                logger.info("质量评审通过，流程完成")
                return f"""# 需求分析完成报告

## 最终文档
{documentation_result}

## 质量评审结果
{review_result}

**评审状态**: ✅ 通过 (得分: {review_summary['total_score']}/100)
**质量等级**: {review_summary['quality_level']}"""
            else:
                logger.warning("质量评审未通过，需要改进")
                return f"""# 需求分析需要改进

## 当前文档
{documentation_result}

## 质量评审意见
{review_result}

**评审状态**: ❌ 需改进 (得分: {review_summary['total_score']}/100)
**质量等级**: {review_summary['quality_level']}

请根据评审意见进行改进后重新提交。"""

        except Exception as e:
            if not await self.handle_error_with_retry(
                e, "质量评审", ErrorSeverity.HIGH, {"stage": "quality_review"}
            ):
                logger.error("质量评审失败且无法重试")
                raise

    async def _parallel_preprocessing(self, user_input: str):
        """并行执行预处理阶段"""
        logger.info("开始并行预处理阶段")

        # 创建并行任务
        try:
            logger.info("创建知识库预处理任务")
            knowledge_task = self._preprocess_with_knowledge_base(user_input)
            logger.info("创建代码分析预处理任务")
            code_task = self._preprocess_with_code_analysis(user_input)

            tasks = [knowledge_task, code_task]
            logger.info(f"创建了 {len(tasks)} 个预处理任务")

            # 并行执行
            logger.info("开始执行并行任务")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("并行任务执行完成")

            # 检查结果中是否有异常
            for i, result in enumerate(results):
                task_name = "知识库预处理" if i == 0 else "代码分析预处理"
                if isinstance(result, Exception):
                    log_exception(logger, f"{task_name}任务失败", result)
                    # 如果是 "READY" 异常，记录更详细的信息
                    if str(result) == "READY":
                        logger.error(f"检测到 READY 异常，来自 {task_name} 任务")
                else:
                    logger.info(f"{task_name}任务成功完成")

            logger.info("并行预处理阶段完成")
        except Exception as e:
            log_exception(logger, "并行预处理阶段失败", e)
            # 如果是 "READY" 异常，记录更详细的信息
            if str(e) == "READY":
                logger.error("检测到 READY 异常，来自并行预处理阶段")
            raise

    async def _parallel_analysis_flow(self) -> str:
        """并行分析流程"""
        try:
            # 更新所有智能体状态为运行中
            for agent_name, agent in self.agents.items():
                await self.collaboration_manager.update_state(
                    agent.id, AgentState.RUNNING, task="并行分析"
                )

            # 创建并行任务
            tasks = []
            clarifier = self.get_agent("clarifier")
            analyst = self.get_agent("analyst")
            writer = self.get_agent("writer")
            reviewer = self.get_agent("reviewer")

            # 启动并行任务
            clarification_task = asyncio.create_task(
                self._clarify_requirements_enhanced(self.current_context["user_input"])
            )
            tasks.append(clarification_task)

            # 等待澄清完成后启动分析
            clarification_result = await clarification_task
            await self.collaboration_manager.share_data(
                clarifier.id, "clarification_result", clarification_result
            )

            analysis_task = asyncio.create_task(
                self._analyze_business_enhanced(clarification_result)
            )
            tasks.append(analysis_task)

            # 等待分析完成后启动文档编写
            analysis_result = await analysis_task
            await self.collaboration_manager.share_data(
                analyst.id, "analysis_result", analysis_result
            )

            documentation_task = asyncio.create_task(
                self._write_documentation_enhanced(analysis_result)
            )
            tasks.append(documentation_task)

            # 等待文档编写完成后启动质量评审
            documentation_result = await documentation_task
            await self.collaboration_manager.share_data(
                writer.id, "documentation_result", documentation_result
            )

            review_task = asyncio.create_task(
                self._quality_review_enhanced(documentation_result)
            )
            tasks.append(review_task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks)

            # 更新所有智能体状态为完成
            for agent_name, agent in self.agents.items():
                await self.collaboration_manager.update_state(
                    agent.id, AgentState.COMPLETED, task="完成"
                )

            return results[-1]  # 返回质量评审结果

        except Exception as e:
            # 更新所有智能体状态为错误
            for agent_name, agent in self.agents.items():
                await self.collaboration_manager.update_state(
                    agent.id, AgentState.ERROR, task="错误"
                )
            raise

    async def _sequential_analysis_flow(self) -> str:
        """顺序分析流程"""
        try:
            # 更新所有智能体状态为等待中
            for agent_name, agent in self.agents.items():
                await self.collaboration_manager.update_state(
                    agent.id, AgentState.WAITING, task="等待"
                )

            # 1. 需求澄清
            clarifier = self.get_agent("clarifier")
            await self.collaboration_manager.update_state(
                clarifier.id, AgentState.RUNNING, task="需求澄清"
            )
            clarification_result = await self._clarify_requirements_enhanced(
                self.current_context["user_input"]
            )
            await self.collaboration_manager.update_state(
                clarifier.id, AgentState.COMPLETED, task="完成"
            )
            await self.collaboration_manager.share_data(
                clarifier.id, "clarification_result", clarification_result
            )

            # 2. 业务分析
            analyst = self.get_agent("analyst")
            await self.collaboration_manager.update_state(
                analyst.id, AgentState.RUNNING, task="业务分析"
            )
            analysis_result = await self._analyze_business_enhanced(
                clarification_result
            )
            await self.collaboration_manager.update_state(
                analyst.id, AgentState.COMPLETED, task="完成"
            )
            await self.collaboration_manager.share_data(
                analyst.id, "analysis_result", analysis_result
            )

            # 3. 文档编写
            writer = self.get_agent("writer")
            await self.collaboration_manager.update_state(
                writer.id, AgentState.RUNNING, task="文档编写"
            )
            documentation_result = await self._write_documentation_enhanced(
                analysis_result
            )
            await self.collaboration_manager.update_state(
                writer.id, AgentState.COMPLETED, task="完成"
            )
            await self.collaboration_manager.share_data(
                writer.id, "documentation_result", documentation_result
            )

            # 4. 质量评审
            reviewer = self.get_agent("reviewer")
            await self.collaboration_manager.update_state(
                reviewer.id, AgentState.RUNNING, task="质量评审"
            )
            review_result = await self._quality_review_enhanced(documentation_result)
            await self.collaboration_manager.update_state(
                reviewer.id, AgentState.COMPLETED, task="完成"
            )

            return review_result

        except Exception as e:
            # 更新所有智能体状态为错误
            for agent_name, agent in self.agents.items():
                await self.collaboration_manager.update_state(
                    agent.id, AgentState.ERROR, task="错误"
                )
            raise

    async def _prepare_quality_review(self, analysis_result: str) -> str:
        """准备质量评审资料（可并行执行）"""
        logger.info("开始准备质量评审资料")

        # 生成质量检查清单
        quality_checklist = self.knowledge_base.get_quality_checklist_for_stage(
            "质量评审"
        )

        # 分析潜在问题
        potential_issues = await self._analyze_potential_issues(analysis_result)

        self.context_manager.add_context_item(
            agent_name="质量评审准备",
            stage="质量评审准备",
            content=f"质量检查清单准备完成，识别潜在问题: {len(potential_issues)}个",
            content_type="quality_preparation",
            metadata={
                "checklist_items": len(quality_checklist),
                "potential_issues": potential_issues,
            },
        )

        logger.info("质量评审资料准备完成")
        return "质量评审准备完成"

    async def _analyze_potential_issues(self, analysis_result: str) -> List[str]:
        """分析潜在问题（支持并行）"""
        # 模拟问题分析
        await asyncio.sleep(0.1)  # 模拟分析时间

        potential_issues = ["需求边界模糊", "性能要求不明确", "用户角色定义不够清晰"]

        return potential_issues

    # ===== 原有方法（优化支持并行） =====

    async def _clarify_requirements(self, user_input: str) -> str:
        """需求澄清阶段"""
        clarifier = self.get_agent("clarifier")

        # 更新智能体记忆
        clarifier.update_memory("user", user_input)

        # 执行澄清步骤
        result = await clarifier.run()

        self.current_context["clarification"] = result
        self.clarification_complete = True

        logger.info("需求澄清阶段完成")
        return result

    async def _analyze_business(self, clarification_result: str) -> str:
        """业务分析阶段"""
        analyst = self.get_agent("analyst")

        # 传递澄清结果
        context_prompt = f"基于以下需求澄清结果进行业务分析：\n\n{clarification_result}"
        analyst.update_memory("system", context_prompt)

        # 执行分析步骤
        result = await analyst.run()

        self.current_context["analysis"] = result
        self.analysis_complete = True

        logger.info("业务分析阶段完成")
        return result

    async def _write_documentation(self, analysis_result: str) -> str:
        """文档编写阶段"""
        writer = self.get_agent("writer")

        # 传递分析结果
        context_prompt = (
            f"基于以下业务分析结果编写需求规格说明书：\n\n{analysis_result}"
        )
        writer.update_memory("system", context_prompt)

        # 执行文档编写
        result = await writer.run()

        self.current_context["documentation"] = result

        logger.info("文档编写阶段完成")
        return result

    async def _quality_review(self, documentation_result: str) -> str:
        """质量评审阶段 - 专业质量把关"""
        reviewer = self.get_agent("reviewer")

        # 传递所有前期成果供评审
        all_results = {
            "澄清结果": self.current_context.get("clarification", ""),
            "分析结果": self.current_context.get("analysis", ""),
            "文档结果": documentation_result,
        }

        context_prompt = f"""请对以下需求分析全套成果进行专业质量评审：

## 需求澄清成果
{all_results['澄清结果']}

## 业务分析成果
{all_results['分析结果']}

## 技术文档成果
{all_results['文档结果']}

请基于软件工程质量标准，进行独立、客观、专业的质量评审。"""

        reviewer.update_memory("system", context_prompt)

        # 执行质量评审
        review_result = await reviewer.run()

        self.current_context["review"] = review_result

        # 检查评审结果，决定是否需要改进
        review_summary = reviewer.get_review_summary()

        if review_summary["total_score"] >= 70:
            logger.info("质量评审通过，流程完成")
            return f"""# 需求分析完成报告

## 最终文档
{documentation_result}

## 质量评审结果
{review_result}

**评审状态**: ✅ 通过 (得分: {review_summary['total_score']}/100)
**质量等级**: {review_summary['quality_level']}"""
        else:
            logger.warning("质量评审未通过，需要改进")
            return f"""# 需求分析需要改进

## 当前文档
{documentation_result}

## 质量评审意见
{review_result}

**评审状态**: ❌ 需改进 (得分: {review_summary['total_score']}/100)
**质量等级**: {review_summary['quality_level']}

请根据评审意见进行改进后重新提交。"""

    async def ask_clarification_question(self, question: str) -> str:
        """处理澄清问题"""
        clarifier = self.get_agent("clarifier")
        clarifier.update_memory("user", question)

        response = await clarifier.step()
        return response

    def get_progress(self) -> Dict:
        """获取流程进度"""
        return {
            "clarification_complete": self.clarification_complete,
            "analysis_complete": self.analysis_complete,
            "current_stage": self._get_current_stage(),
            "context": self.current_context,
            "parallel_enabled": self.enable_parallel,
        }

    def _get_current_stage(self) -> str:
        """获取当前阶段"""
        if not self.clarification_complete:
            return "需求澄清"
        elif not self.analysis_complete:
            return "业务分析"
        else:
            return "文档编写"

    # ==== 增强方法实现 ====

    async def _preprocess_with_knowledge_base(self, user_input: str):
        """使用知识库预处理"""
        logger.info("开始知识库预处理")
        try:
            # 搜索相关知识
            logger.info("开始搜索相关知识")
            results = await self.knowledge_base.search(user_input, top_k=5)
            logger.info(f"知识库搜索完成，找到 {len(results) if results else 0} 条结果")

            if results:
                # 将知识添加到上下文
                logger.info("将知识添加到上下文")
                knowledge_context = []
                for result in results:
                    knowledge_context.append(
                        {
                            "content": result["content"],
                            "similarity": result["similarity"],
                        }
                    )

                try:
                    logger.info("更新全局状态：知识上下文")
                    self.context_manager.update_global_state(
                        "knowledge_context", knowledge_context
                    )
                    logger.info("全局状态更新成功")
                except Exception as e:
                    log_exception(logger, "更新全局状态失败", e)
                    # 继续执行，不抛出异常

                # 将知识添加到所有智能体的内存
                logger.info("将知识添加到所有智能体的内存")
                for agent in self.agents.values():
                    try:
                        agent.memory.add_message(
                            Message.system_message(
                                "相关知识:\n"
                                + "\n".join(
                                    f"- {item['content']} (相关度: {item['similarity']:.2f})"
                                    for item in knowledge_context
                                )
                            )
                        )
                    except Exception as e:
                        log_exception(
                            logger, f"添加知识到智能体 {agent.name} 的内存失败", e
                        )
                        # 继续执行，不抛出异常
                logger.info("知识已添加到所有智能体的内存")

            # 添加新知识
            logger.info("将用户需求添加到知识库")
            try:
                await self.knowledge_base.add(
                    {
                        "title": "用户需求",
                        "content": user_input,
                        "type": "requirement",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                logger.info("用户需求已添加到知识库")
            except Exception as e:
                log_exception(logger, "添加用户需求到知识库失败", e)
                # 继续执行，不抛出异常

            logger.info("知识库预处理完成")
            return True

        except Exception as e:
            log_exception(logger, "知识库预处理失败", e)
            # 如果是 "READY" 异常，记录更详细的信息
            if str(e) == "READY":
                logger.error("检测到 READY 异常，来自知识库预处理")
            raise

    async def _preprocess_with_code_analysis(self, user_input: str):
        """使用代码分析预处理"""
        logger.info("开始代码分析预处理")
        try:
            # 分析代码库
            logger.info("开始分析代码库")
            analysis_result = self.code_analyzer.analyze_codebase(
                codebase_id="temp",
                root_path=self.project_root or ".",
            )
            logger.info("代码库分析完成")

            if analysis_result:
                # 提取关键信息
                logger.info("提取代码分析关键信息")
                try:
                    code_context = {
                        "total_files": analysis_result.file_count,
                        "languages": analysis_result.languages,
                        "components": [
                            {
                                "name": comp.name,
                                "type": (
                                    comp.type.value
                                    if hasattr(comp.type, "value")
                                    else comp.type
                                ),
                                "file": comp.file_path,
                                "complexity": (
                                    comp.complexity.value
                                    if hasattr(comp.complexity, "value")
                                    else comp.complexity
                                ),
                            }
                            for comp in analysis_result.components[
                                :10
                            ]  # 只取前10个组件
                        ],
                        "technical_debts": [
                            {
                                "title": issue.title,
                                "description": issue.description,
                                "severity": issue.severity,
                            }
                            for issue in analysis_result.quality_issues[
                                :5
                            ]  # 只取前5个问题
                        ],
                        "complexity_analysis": {
                            "overall_complexity": analysis_result.metrics.cyclomatic_complexity,
                            "maintainability_index": analysis_result.metrics.maintainability_index,
                        },
                    }
                    logger.info("代码分析关键信息提取完成")
                except Exception as e:
                    logger.error(f"提取代码分析关键信息失败: {str(e)}")
                    # 创建一个简化的上下文
                    code_context = {
                        "total_files": analysis_result.file_count,
                        "languages": analysis_result.languages,
                        "components": [],
                        "technical_debts": [],
                        "complexity_analysis": {},
                    }
                    logger.info("使用简化的代码上下文")

                # 更新上下文
                try:
                    logger.info("更新全局状态：代码上下文")
                    self.context_manager.update_global_state(
                        "code_context", code_context
                    )
                    logger.info("全局状态更新成功")
                except Exception as e:
                    logger.error(f"更新全局状态失败: {str(e)}")
                    # 继续执行，不抛出异常

                # 将代码分析结果添加到所有智能体的内存
                try:
                    logger.info("创建代码分析摘要")
                    summary = (
                        f"代码分析结果:\n"
                        f"- 总文件数: {code_context['total_files']}\n"
                        f"- 使用的语言: {', '.join(code_context['languages'].keys())}\n"
                        f"- 主要组件: {', '.join(comp['name'] for comp in code_context['components'])}\n"
                        f"- 技术债务: {len(code_context['technical_debts'])} 个问题\n"
                        f"- 整体复杂度: {code_context['complexity_analysis'].get('overall_complexity', 'N/A')}"
                    )
                    logger.info("代码分析摘要创建完成")
                except Exception as e:
                    logger.error(f"创建代码分析摘要失败: {str(e)}")
                    summary = "代码分析结果: 无法生成详细摘要"

                logger.info("将代码分析结果添加到所有智能体的内存")
                for agent in self.agents.values():
                    try:
                        agent.memory.add_message(Message.system_message(summary))
                        logger.info(f"代码分析结果已添加到智能体 {agent.name} 的内存")
                    except Exception as e:
                        logger.error(
                            f"添加代码分析结果到智能体 {agent.name} 的内存失败: {str(e)}"
                        )
                        # 继续执行，不抛出异常

            logger.info("代码分析预处理完成")
            return True

        except Exception as e:
            logger.error(f"代码分析预处理失败: {str(e)}")
            # 如果是 "READY" 异常，记录更详细的信息
            if str(e) == "READY":
                logger.error("检测到 READY 异常，来自代码分析预处理")
            return False

    async def _generate_final_report(self) -> str:
        """生成最终报告"""
        # 生成最终会话摘要
        session_summary = self.context_manager.get_session_summary()

        # 获取质量指标
        quality_metrics = self._get_quality_metrics()

        # 构建最终报告
        final_report = {
            "session_summary": session_summary,
            "quality_metrics": quality_metrics,
            "context_items": self.context_manager.context_items[-10:],
            "parallel_enabled": self.enable_parallel,
        }

        logger.info("最终报告生成完成")
        return final_report

    def _get_quality_metrics(self) -> Dict:
        """获取质量指标"""
        return {
            "clarity_score": self.context_manager.global_state.get("clarity_score", 0),
            "business_complexity": self.context_manager.global_state.get(
                "business_complexity", "未知"
            ),
            "document_completeness": self.context_manager.global_state.get(
                "document_completeness", 0
            ),
            "quality_score": self.context_manager.global_state.get("quality_score", 0),
            "total_context_items": len(self.context_manager.context_items),
            "session_duration": str(
                self.context_manager.get_session_summary().get(
                    "session_duration", "未知"
                )
            ),
        }

    async def generate_clarification_question(
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
            logger.info(f"生成澄清问题: {requirement[:50]}...")

            # 初始化上下文
            ctx = context or {}
            ctx["session_id"] = self.session_id

            # 获取澄清师智能体
            clarifier = self.agents["clarifier"]

            # 清除之前的内存
            clarifier.memory.clear()

            # 添加需求到内存
            clarifier.memory.add_message(Message.user_message(requirement))

            # 使用知识库增强上下文
            if self.knowledge_base:
                try:
                    await self._preprocess_with_knowledge_base(requirement)
                except Exception as e:
                    logger.warning(f"知识库增强失败: {e}")

            # 生成澄清问题
            result = await clarifier.step(requirement)

            # 获取问题列表
            questions = clarifier.questions if hasattr(clarifier, "questions") else []
            if not questions and result:
                # 尝试从结果中提取问题
                import re

                questions = re.findall(
                    r"\d+\.\s*(.*?)\s*(?=\d+\.|$)", result, re.DOTALL
                )
                questions = [q.strip() for q in questions if q.strip()]

            # 如果还是没有问题，生成一个默认问题
            if not questions:
                questions = ["请详细描述您的需求是什么？"]

            # 更新上下文
            ctx["requirement"] = requirement
            ctx["questions"] = questions

            return {"questions": questions, "status": "success", "context": ctx}
        except Exception as e:
            logger.error(f"生成澄清问题失败: {e}")
            raise

    async def process_clarification_answer(
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
            logger.info(f"处理澄清答案: {question[:30]}... -> {answer[:30]}...")

            # 初始化上下文
            ctx = context or {}
            ctx["session_id"] = self.session_id

            # 获取澄清师智能体
            clarifier = self.agents["clarifier"]

            # 添加问答到内存
            clarifier.memory.add_message(
                Message.user_message(f"问题: {question}\n回答: {answer}")
            )

            # 处理答案
            result = await clarifier.process_answer(question, answer)

            # 生成新问题
            new_questions = (
                clarifier.generate_followup_questions()
                if hasattr(clarifier, "generate_followup_questions")
                else []
            )

            # 如果没有后续问题，可能澄清已完成
            is_complete = len(new_questions) == 0

            # 更新上下文
            ctx["requirement"] = ctx.get("requirement", "")
            ctx["questions"] = new_questions
            ctx["is_complete"] = is_complete

            return {
                "questions": new_questions,
                "status": "complete" if is_complete else "in_progress",
                "context": ctx,
            }
        except Exception as e:
            logger.error(f"处理澄清答案失败: {e}")
            raise
