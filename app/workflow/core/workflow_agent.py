"""
工作流智能体基类

提供基于工作流引擎的智能体基础实现：
- 事件驱动机制
- 状态管理
- 工具集成
- 内存管理
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from loguru import logger

from app.workflow.core.workflow_context import WorkflowContext
from app.workflow.core.workflow_result import WorkflowResult
from app.workflow.core.workflow_error import WorkflowError
from app.workflow.engine.event_bus import EventBus
from app.llm import LLM


class AgentState(Enum):
    """智能体状态"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    ERROR = "error"


class WorkflowAgent:
    """工作流智能体基类"""

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        workflow_context: WorkflowContext,
        event_bus: EventBus,
        llm: Optional[LLM] = None,
        **kwargs
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.context = workflow_context
        self.event_bus = event_bus
        self.llm = llm or LLM()

        self.state = AgentState.INITIALIZED
        self.memory: List[Dict[str, Any]] = []
        self.current_step = 0
        self.max_steps = kwargs.get("max_steps", 5)
        self.metadata: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """初始化智能体"""
        try:
            # 注册事件监听
            self.event_bus.subscribe(f"{self.name}_start", self.on_start)
            self.event_bus.subscribe(f"{self.name}_pause", self.on_pause)
            self.event_bus.subscribe(f"{self.name}_resume", self.on_resume)
            self.event_bus.subscribe(f"{self.name}_stop", self.on_stop)

            # 初始化状态
            self.state = AgentState.INITIALIZED
            self.current_step = 0
            self.memory.clear()

            # 发布初始化完成事件
            await self.event_bus.publish(
                f"{self.name}_initialized",
                {"agent": self.name, "state": self.state.value}
            )

        except Exception as e:
            logger.error(f"智能体初始化失败: {e}")
            self.state = AgentState.ERROR
            raise WorkflowError(f"智能体初始化失败: {str(e)}")

    async def execute(self, input_data: Any = None) -> WorkflowResult:
        """执行智能体任务"""
        try:
            self.state = AgentState.RUNNING

            # 发布开始执行事件
            await self.event_bus.publish(
                f"{self.name}_execution_started",
                {"agent": self.name, "input": input_data}
            )

            # 执行步骤
            result = await self.step(input_data)

            # 更新上下文
            self.context.update({
                f"{self.name}_result": result,
                f"{self.name}_state": self.state.value
            })

            # 发布执行完成事件
            await self.event_bus.publish(
                f"{self.name}_execution_completed",
                {"agent": self.name, "result": result}
            )

            return WorkflowResult(
                success=True,
                data=result,
                metadata={
                    "agent": self.name,
                    "state": self.state.value,
                    "step": self.current_step
                }
            )

        except Exception as e:
            logger.error(f"智能体执行失败: {e}")
            self.state = AgentState.ERROR

            # 发布错误事件
            await self.event_bus.publish(
                f"{self.name}_execution_error",
                {"agent": self.name, "error": str(e)}
            )

            raise WorkflowError(f"智能体执行失败: {str(e)}")

    async def step(self, input_data: Any = None) -> Any:
        """执行单个步骤（由子类实现）"""
        raise NotImplementedError("子类必须实现step方法")

    def update_memory(self, role: str, content: str) -> None:
        """更新对话历史"""
        self.memory.append({"role": role, "content": content})

    def get_memory(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.memory

    def clear_memory(self) -> None:
        """清空对话历史"""
        self.memory.clear()

    async def on_start(self, event_data: Dict[str, Any]) -> None:
        """开始事件处理"""
        self.state = AgentState.RUNNING
        logger.info(f"智能体 {self.name} 开始执行")

    async def on_pause(self, event_data: Dict[str, Any]) -> None:
        """暂停事件处理"""
        self.state = AgentState.PAUSED
        logger.info(f"智能体 {self.name} 已暂停")

    async def on_resume(self, event_data: Dict[str, Any]) -> None:
        """恢复事件处理"""
        self.state = AgentState.RUNNING
        logger.info(f"智能体 {self.name} 已恢复")

    async def on_stop(self, event_data: Dict[str, Any]) -> None:
        """停止事件处理"""
        self.state = AgentState.FINISHED
        logger.info(f"智能体 {self.name} 已停止")

    def get_state(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "metadata": self.metadata
        }

    def __str__(self) -> str:
        return f"{self.name} ({self.state.value})"
