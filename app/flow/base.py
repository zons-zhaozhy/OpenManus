import traceback
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.agent.base import BaseAgent
from app.assistants.requirements.collaboration_manager import CollaborationManager
from app.flow.state import FlowState, FlowStateManager
from app.logger import log_exception, logger


class BaseFlow(BaseModel):
    """Base class for execution flows supporting multiple agents"""

    agents: Dict[str, BaseAgent]
    tools: Optional[List] = None
    primary_agent_key: Optional[str] = None
    state_manager: FlowStateManager = Field(default_factory=FlowStateManager)
    collaboration_manager: Optional[CollaborationManager] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self, agents: Union[BaseAgent, List[BaseAgent], Dict[str, BaseAgent]], **data
    ):
        # Handle different ways of providing agents
        if isinstance(agents, BaseAgent):
            agents_dict = {"default": agents}
        elif isinstance(agents, list):
            agents_dict = {f"agent_{i}": agent for i, agent in enumerate(agents)}
        else:
            agents_dict = agents

        # If primary agent not specified, use first agent
        primary_key = data.get("primary_agent_key")
        if not primary_key and agents_dict:
            primary_key = next(iter(agents_dict))
            data["primary_agent_key"] = primary_key

        # Initialize state manager if provided
        if "state_manager" in data:
            data["state_manager"] = FlowStateManager(**data["state_manager"])

        # Initialize collaboration manager if not provided
        if "collaboration_manager" not in data or data["collaboration_manager"] is None:
            data["collaboration_manager"] = CollaborationManager()

        # Set the agents dictionary
        data["agents"] = agents_dict

        # Initialize using BaseModel's init
        super().__init__(**data)

        # Register all agents with the collaboration manager
        for agent_key, agent in self.agents.items():
            if not self.collaboration_manager.is_agent_registered(agent.id):
                success = self.collaboration_manager.register_agent_sync(agent)
                if not success:
                    logger.error(
                        f"Failed to register agent {agent.id} with collaboration manager"
                    )
                    raise ValueError(f"Failed to register agent {agent.id}")

    @property
    def primary_agent(self) -> Optional[BaseAgent]:
        """Get the primary agent for the flow"""
        return self.agents.get(self.primary_agent_key)

    def get_agent(self, key: str) -> Optional[BaseAgent]:
        """Get a specific agent by key"""
        agent = self.agents.get(key)
        if agent and not self.collaboration_manager.is_agent_registered(agent.id):
            success = self.collaboration_manager.register_agent_sync(agent)
            if not success:
                logger.error(
                    f"Failed to register agent {agent.id} with collaboration manager"
                )
                raise ValueError(f"Failed to register agent {agent.id}")
        return agent

    def add_agent(self, key: str, agent: BaseAgent) -> None:
        """Add a new agent to the flow"""
        if not self.collaboration_manager.is_agent_registered(agent.id):
            success = self.collaboration_manager.register_agent_sync(agent)
            if not success:
                logger.error(
                    f"Failed to register agent {agent.id} with collaboration manager"
                )
                raise ValueError(f"Failed to register agent {agent.id}")
        self.agents[key] = agent

    def get_state(self) -> str:
        """Get current flow state"""
        return self.state_manager.current_state

    def is_running(self) -> bool:
        """Check if flow is in running state"""
        return self.state_manager.current_state == FlowState.RUNNING.value

    def is_completed(self) -> bool:
        """Check if flow is completed"""
        return self.state_manager.current_state == FlowState.COMPLETED.value

    def is_failed(self) -> bool:
        """Check if flow has failed"""
        return self.state_manager.current_state == FlowState.FAILED.value

    def can_proceed(self) -> bool:
        """Check if flow can proceed"""
        return self.state_manager.can_proceed()

    def get_error_info(self) -> Dict[str, Union[int, str]]:
        """Get error information"""
        return {
            "error_count": self.state_manager.error_count,
            "last_error": self.state_manager.last_error,
        }

    def reset(self) -> None:
        """Reset flow state"""
        self.state_manager = FlowStateManager()

    async def initialize_flow(self, input_text: str) -> None:
        """
        初始化流程，捕获可能的异常

        Args:
            input_text: 输入文本
        """
        try:
            logger.info(
                f"开始{self.__class__.__name__}流程 - 输入: {input_text[:50]}..."
            )

            # 检查流程状态
            if self.state_manager.current_state != FlowState.INITIALIZED.value:
                logger.warning(
                    f"流程状态不是 INITIALIZED，当前状态: {self.state_manager.current_state}"
                )
                self.state_manager.transition_to(FlowState.INITIALIZED.value)

            # 确保所有智能体都已注册
            for agent_key, agent in self.agents.items():
                if not self.collaboration_manager.is_agent_registered(agent.id):
                    success = self.collaboration_manager.register_agent_sync(agent)
                    if not success:
                        raise ValueError(f"Failed to register agent {agent.id}")

            # 设置流程状态为 READY
            try:
                self.state_manager.transition_to(FlowState.READY.value)
                logger.info(f"流程状态已设置为 READY")
            except Exception as e:
                log_exception(logger, "设置流程状态为 READY 失败", e)
                # 如果是 "READY" 异常，记录更详细的信息
                if str(e) == "READY":
                    logger.error(
                        f"检测到 READY 异常，来自 {self.__class__.__name__}.initialize_flow"
                    )
                    logger.error(f"堆栈跟踪: {traceback.format_exc()}")
                raise

        except Exception as e:
            log_exception(logger, f"{self.__class__.__name__}初始化失败", e)
            # 如果是 "READY" 异常，记录更详细的信息
            if str(e) == "READY":
                logger.error(
                    f"检测到 READY 异常，来自 {self.__class__.__name__}.initialize_flow"
                )
                logger.error(f"堆栈跟踪: {traceback.format_exc()}")
            raise

    async def execute(self, input_text: str) -> Union[str, Dict[str, Any]]:
        """Execute the flow with given input"""
        try:
            # 确保流程已初始化
            if self.state_manager.current_state == FlowState.INITIALIZED.value:
                await self.initialize_flow(input_text)

            # 确保流程处于READY状态
            if self.state_manager.current_state != FlowState.READY.value:
                raise ValueError("Flow must be in READY state before execution")

            # 转换到RUNNING状态
            self.state_manager.transition_to(FlowState.RUNNING.value)

            # 子类实现具体执行逻辑
            result = await self._execute_impl(input_text)

            # 如果执行成功，转换到COMPLETED状态
            self.state_manager.transition_to(FlowState.COMPLETED.value)

            return result

        except Exception as e:
            # 记录错误并转换到FAILED状态
            self.state_manager.record_error(str(e))
            if not self.state_manager.is_terminal():
                self.state_manager.transition_to(FlowState.FAILED.value)
            raise

    async def _execute_impl(self, input_text: str) -> Union[str, Dict[str, Any]]:
        """Implement the actual execution logic in subclasses"""
        # 默认实现，子类可以覆盖
        return {"status": "success", "message": "Base flow execution completed"}
