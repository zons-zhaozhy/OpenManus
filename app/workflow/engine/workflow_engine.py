"""
工作流引擎

负责工作流的执行和管理
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from app.workflow.agents.business_analyst import BusinessAnalystAgent
from app.workflow.agents.quality_reviewer import QualityReviewerAgent
from app.workflow.agents.requirement_clarifier import RequirementClarifierAgent
from app.workflow.agents.requirements_analyzer import RequirementsAnalyzerAgent
from app.workflow.agents.technical_writer import TechnicalWriterAgent

from ..core.workflow_context import WorkflowContext
from ..core.workflow_definition import WorkflowDefinition
from ..core.workflow_error import WorkflowError, WorkflowNotFoundError
from ..core.workflow_event import WorkflowEvent
from ..core.workflow_result import WorkflowResult
from ..core.workflow_step import WorkflowStep
from .event_bus import EventBus
from .state_store import StateStore


class WorkflowEngine:
    """工作流引擎"""

    def __init__(
        self,
        state_store: StateStore,
        event_bus: EventBus,
        max_concurrent_workflows: int = 10,
        max_retries: int = 3,
        step_timeout: int = 300,
    ):
        self.state_store = state_store
        self.event_bus = event_bus
        self.max_concurrent_workflows = max_concurrent_workflows
        self.max_retries = max_retries
        self.step_timeout = step_timeout
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._running_workflows: Dict[str, WorkflowContext] = {}
        self._agents: Dict[str, Dict[str, Any]] = {
            "requirements_analyzer": {
                "class": RequirementsAnalyzerAgent,
                "config": {"name": "需求分析师"},
            },
            "requirement_clarifier": {
                "class": RequirementClarifierAgent,
                "config": {"name": "需求澄清师"},
            },
            "business_analyst": {
                "class": BusinessAnalystAgent,
                "config": {"name": "业务分析师"},
            },
            "quality_reviewer": {
                "class": QualityReviewerAgent,
                "config": {"name": "质量审查员"},
            },
            "technical_writer": {
                "class": TechnicalWriterAgent,
                "config": {"name": "技术文档专家"},
            },
        }

    async def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """注册工作流定义"""
        if workflow.id in self._workflows:
            raise WorkflowError(f"工作流已存在: {workflow.id}")
        self._workflows[workflow.id] = workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        context: Optional[WorkflowContext] = None,
    ) -> WorkflowResult:
        """执行工作流"""
        try:
            # 获取工作流定义
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                raise WorkflowNotFoundError(f"工作流不存在: {workflow_id}")

            # 创建或使用上下文
            if not context:
                context = WorkflowContext(
                    workflow_id=workflow_id,
                    execution_id=f"exec_{workflow_id}_{int(datetime.now().timestamp())}",
                    status="pending",
                    start_time=datetime.now(),
                    data=input_data,
                )

            # 检查并限制并发工作流数量
            if len(self._running_workflows) >= self.max_concurrent_workflows:
                raise WorkflowError("超出最大并发工作流数量限制")

            # 记录运行中的工作流
            self._running_workflows[workflow_id] = context

            try:
                # 发布工作流开始事件
                await self.event_bus.publish(
                    WorkflowEvent.WORKFLOW_STARTED,
                    {
                        "workflow_id": workflow_id,
                        "execution_id": context.execution_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                # 执行工作流步骤
                result = await self._execute_workflow_steps(workflow, context)

                # 发布工作流完成事件
                await self.event_bus.publish(
                    WorkflowEvent.WORKFLOW_COMPLETED,
                    {
                        "workflow_id": workflow_id,
                        "execution_id": context.execution_id,
                        "result": result.dict(),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                return result

            finally:
                # 清理运行中的工作流
                del self._running_workflows[workflow_id]

        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            # 发布工作流失败事件
            await self.event_bus.publish(
                WorkflowEvent.WORKFLOW_FAILED,
                {
                    "workflow_id": workflow_id,
                    "execution_id": context.execution_id if context else None,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                },
            )
            raise

    async def _execute_workflow_steps(
        self, workflow: WorkflowDefinition, context: WorkflowContext
    ) -> WorkflowResult:
        """执行工作流步骤"""
        try:
            # 获取工作流步骤
            steps = workflow.get_ordered_steps()
            if not steps:
                raise WorkflowError("工作流没有定义步骤")

            # 初始化结果
            result = WorkflowResult(
                workflow_id=workflow.id,
                execution_id=context.execution_id,
                start_time=context.start_time,
                end_time=None,
                status="running",
                steps_results={},
            )

            # 执行每个步骤
            for step in steps:
                # 检查步骤依赖是否满足
                if not self._check_step_dependencies(step, result):
                    raise WorkflowError(f"步骤依赖未满足: {step.name}")

                # 创建智能体
                agent = await self._create_agent(step.agent_type, context)

                # 准备步骤输入
                step_input = self._prepare_step_input(step, context, result)

                # 执行步骤
                step_result = await self._execute_step(step, agent, step_input)

                # 更新结果
                result.steps_results[step.name] = step_result
                context.data.update(step_result)

                # 发布步骤完成事件
                await self.event_bus.publish(
                    WorkflowEvent.STEP_COMPLETED,
                    {
                        "workflow_id": workflow.id,
                        "execution_id": context.execution_id,
                        "step_name": step.name,
                        "result": step_result,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # 更新工作流结果
            result.end_time = datetime.now()
            result.status = "completed"

            return result

        except Exception as e:
            logger.error(f"工作流步骤执行失败: {e}")
            raise

    async def _create_agent(
        self, agent_type: str, context: WorkflowContext
    ) -> Optional[Any]:
        """创建智能体实例"""
        agent_info = self._agents.get(agent_type)
        if not agent_info:
            raise WorkflowError(f"未找到智能体类型: {agent_type}")

        agent_class = agent_info["class"]
        agent_config = agent_info.get("config", {})

        return agent_class(
            workflow_context=context, event_bus=self.event_bus, **agent_config
        )

    def _check_step_dependencies(
        self, step: WorkflowStep, result: WorkflowResult
    ) -> bool:
        """检查步骤依赖是否满足"""
        for dep in step.dependencies:
            if dep not in result.steps_results:
                return False
        return True

    def _prepare_step_input(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        result: WorkflowResult,
    ) -> Dict[str, Any]:
        """准备步骤输入数据"""
        step_input = {}

        # 添加必需的输入
        for input_name in step.required_inputs:
            if input_name in context.data:
                step_input[input_name] = context.data[input_name]
            else:
                raise WorkflowError(f"缺少必需的输入: {input_name}")

        # 添加可选输入
        for input_name in step.optional_inputs:
            if input_name in context.data:
                step_input[input_name] = context.data[input_name]

        return step_input

    async def _execute_step(
        self,
        step: WorkflowStep,
        agent: Any,
        step_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行工作流步骤"""
        try:
            # 设置超时
            async with asyncio.timeout(self.step_timeout):
                # 执行步骤
                result = await agent.execute(step_input)

                # 验证输出
                self._validate_step_output(step, result)

                return result

        except asyncio.TimeoutError:
            raise WorkflowError(f"步骤执行超时: {step.name}")
        except Exception as e:
            raise WorkflowError(f"步骤执行失败: {step.name}, 错误: {e}")

    def _validate_step_output(self, step: WorkflowStep, output: Dict[str, Any]) -> None:
        """验证步骤输出"""
        for output_name in step.outputs:
            if output_name not in output:
                raise WorkflowError(f"缺少必需的输出: {output_name}")

    async def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        return await self.state_store.get_workflow_state(workflow_id)

    async def update_workflow_state(
        self, workflow_id: str, state: Dict[str, Any]
    ) -> None:
        """更新工作流状态"""
        await self.state_store.save_workflow_state(workflow_id, state)
