"""
需求分析工作流服务

提供高层次的工作流管理服务，协调各个组件的工作
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.workflow.agents.business_analyst import BusinessAnalystAgent
from app.workflow.agents.quality_reviewer import QualityReviewerAgent
from app.workflow.agents.requirement_clarifier import RequirementClarifierAgent
from app.workflow.agents.requirements_analyzer import RequirementsAnalyzerAgent
from app.workflow.agents.technical_writer import TechnicalWriterAgent
from app.workflow.core.workflow_context import WorkflowContext
from app.workflow.core.workflow_state import WorkflowState
from app.workflow.engine.event_bus import EventBus
from app.workflow.engine.state_store import StateStore
from app.workflow.engine.workflow_engine import WorkflowEngine

from ..models import WorkflowError
from ..storage import WorkflowStorage


class WorkflowService:
    """工作流服务"""

    def __init__(self):
        """初始化工作流服务"""
        # 创建工作流引擎依赖
        self.state_store = StateStore()
        self.event_bus = EventBus()

        # 创建工作流引擎
        self.engine = WorkflowEngine(
            state_store=self.state_store,
            event_bus=self.event_bus,
            max_concurrent_workflows=10,
        )
        self.storage = WorkflowStorage()

    async def create_workflow(
        self,
        project_id: str,
        initial_requirements: str,
        user_id: str,
        workflow_type: str = "requirements_analysis",
    ) -> Dict:
        """创建新的工作流"""
        try:
            # 创建工作流上下文
            context = await self._create_workflow_context(
                project_id=project_id,
                initial_requirements=initial_requirements,
                user_id=user_id,
                workflow_type=workflow_type,
            )

            # 初始化智能体
            agents = await self._initialize_agents(context)

            # 配置工作流
            workflow_config = await self._create_workflow_config(
                context=context, agents=agents, workflow_type=workflow_type
            )

            # 启动工作流
            workflow_id = await self.engine.create_workflow(
                context=context, config=workflow_config
            )

            # 记录工作流元数据
            await self._record_workflow_metadata(
                workflow_id=workflow_id, context=context, config=workflow_config
            )

            return {
                "workflow_id": workflow_id,
                "status": "created",
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"创建工作流失败: {e}")
            raise WorkflowError(f"创建工作流失败: {str(e)}")

    async def _create_workflow_context(
        self,
        project_id: str,
        initial_requirements: str,
        user_id: str,
        workflow_type: str,
    ) -> WorkflowContext:
        """创建工作流上下文"""
        try:
            context = WorkflowContext(
                project_id=project_id,
                user_id=user_id,
                workflow_type=workflow_type,
                initial_requirements=initial_requirements,
                created_at=datetime.utcnow().isoformat(),
            )

            # 添加项目相关信息
            project_info = await self._fetch_project_info(project_id)
            context.update({"project_info": project_info})

            # 添加用户相关信息
            user_info = await self._fetch_user_info(user_id)
            context.update({"user_info": user_info})

            return context

        except Exception as e:
            logger.error(f"创建工作流上下文失败: {e}")
            raise WorkflowError(f"创建工作流上下文失败: {str(e)}")

    async def _initialize_agents(self, context: WorkflowContext) -> List[Any]:
        """初始化智能体"""
        try:
            agents = []

            # 创建需求分析智能体
            analyzer = RequirementsAnalyzerAgent(
                workflow_context=context, event_bus=self.engine.event_bus
            )
            agents.append(analyzer)

            # 创建需求澄清智能体
            clarifier = RequirementClarifierAgent(
                workflow_context=context, event_bus=self.engine.event_bus
            )
            agents.append(clarifier)

            # 创建业务分析智能体
            analyst = BusinessAnalystAgent(
                workflow_context=context, event_bus=self.engine.event_bus
            )
            agents.append(analyst)

            # 创建技术文档编写智能体
            writer = TechnicalWriterAgent(
                workflow_context=context, event_bus=self.engine.event_bus
            )
            agents.append(writer)

            # 创建质量审查智能体
            reviewer = QualityReviewerAgent(
                workflow_context=context, event_bus=self.engine.event_bus
            )
            agents.append(reviewer)

            return agents

        except Exception as e:
            logger.error(f"初始化智能体失败: {e}")
            raise WorkflowError(f"初始化智能体失败: {str(e)}")

    async def _create_workflow_config(
        self, context: WorkflowContext, agents: List[Any], workflow_type: str
    ) -> Dict:
        """创建工作流配置"""
        try:
            config = {
                "type": workflow_type,
                "agents": [agent.name for agent in agents],
                "steps": [
                    {
                        "name": "requirement_clarification",
                        "agent": "需求澄清专家",
                        "description": "澄清和细化需求",
                    },
                    {
                        "name": "business_analysis",
                        "agent": "业务分析专家",
                        "description": "分析业务价值和场景",
                    },
                    {
                        "name": "technical_documentation",
                        "agent": "技术文档编写师",
                        "description": "编写技术文档",
                    },
                    {
                        "name": "quality_review",
                        "agent": "质量审查专家",
                        "description": "审查文档质量",
                    },
                ],
                "transitions": [
                    {
                        "from": "requirement_clarification",
                        "to": "business_analysis",
                        "condition": "clarification_complete",
                    },
                    {
                        "from": "business_analysis",
                        "to": "technical_documentation",
                        "condition": "analysis_complete",
                    },
                    {
                        "from": "technical_documentation",
                        "to": "quality_review",
                        "condition": "documentation_complete",
                    },
                ],
            }

            return config

        except Exception as e:
            logger.error(f"创建工作流配置失败: {e}")
            raise WorkflowError(f"创建工作流配置失败: {str(e)}")

    async def _record_workflow_metadata(
        self, workflow_id: str, context: WorkflowContext, config: Dict
    ) -> None:
        """记录工作流元数据"""
        try:
            metadata = {
                "workflow_id": workflow_id,
                "context": context.to_dict(),
                "config": config,
                "created_at": datetime.utcnow().isoformat(),
                "status": "created",
                "version": "1.0",
            }

            await self.storage.save_workflow_metadata(
                workflow_id=workflow_id, metadata=metadata
            )

        except Exception as e:
            logger.error(f"记录工作流元数据失败: {e}")
            raise WorkflowError(f"记录工作流元数据失败: {str(e)}")

    async def _fetch_project_info(self, project_id: str) -> Dict:
        """获取项目信息"""
        # TODO: 实现项目信息获取逻辑
        return {"id": project_id, "name": "示例项目", "description": "这是一个示例项目"}

    async def _fetch_user_info(self, user_id: str) -> Dict:
        """获取用户信息"""
        # TODO: 实现用户信息获取逻辑
        return {"id": user_id, "name": "示例用户", "role": "项目经理"}
