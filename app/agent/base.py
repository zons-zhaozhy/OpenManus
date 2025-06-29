import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.llm import LLM
from app.logger import logger

# 可选导入sandbox，如果不可用则设为None
try:
    from app.sandbox.client import SANDBOX_CLIENT
except (ImportError, ModuleNotFoundError) as e:
    print(f"警告: Sandbox功能不可用 ({e})，将禁用相关功能")
    SANDBOX_CLIENT = None
from app.schema import ROLE_TYPE, AgentState, Memory, Message


class BaseAgent(BaseModel, ABC):
    """Abstract base class for managing agent state and execution.

    Provides foundational functionality for state transitions, memory management,
    and a step-based execution loop. Subclasses must implement the `step` method.
    """

    # Core attributes
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique ID of the agent"
    )
    name: str = Field(..., description="Unique name of the agent")
    description: Optional[str] = Field(None, description="Optional agent description")

    # Prompts
    system_prompt: Optional[str] = Field(
        None, description="System-level instruction prompt"
    )
    next_step_prompt: Optional[str] = Field(
        None, description="Prompt for determining next action"
    )

    # Dependencies
    llm: LLM = Field(default_factory=LLM, description="Language model instance")
    memory: Memory = Field(default_factory=Memory, description="Agent's memory store")
    state: AgentState = Field(
        default=AgentState.IDLE, description="Current agent state"
    )

    # Execution control
    max_steps: int = Field(default=10, description="Maximum steps before termination")
    current_step: int = Field(default=0, description="Current step in execution")

    duplicate_threshold: int = 2

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # Allow extra fields for flexibility in subclasses

    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """Initialize agent with default settings if not provided."""
        if self.llm is None or not isinstance(self.llm, LLM):
            self.llm = LLM(config_name=self.name.lower())
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self

    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """Context manager for safe agent state transitions.

        Args:
            new_state: The state to transition to during the context.

        Yields:
            None: Allows execution within the new state.

        Raises:
            ValueError: If the new_state is invalid.
        """
        if not isinstance(new_state, AgentState):
            raise ValueError(f"Invalid state: {new_state}")

        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR  # Transition to ERROR on failure
            raise e
        finally:
            self.state = previous_state  # Revert to previous state

    def update_memory(
        self,
        role: ROLE_TYPE,  # type: ignore
        content: str,
        base64_image: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Add a message to the agent's memory.

        Args:
            role: The role of the message sender (user, system, assistant, tool).
            content: The message content.
            base64_image: Optional base64 encoded image.
            **kwargs: Additional arguments (e.g., tool_call_id for tool messages).

        Raises:
            ValueError: If the role is unsupported.
        """
        if role not in ["user", "system", "assistant", "tool"]:
            raise ValueError(f"Unsupported message role: {role}")

        # Create message with appropriate parameters based on role
        if role == "user":
            message = Message.user_message(content, base64_image)
        elif role == "system":
            message = Message.system_message(
                content
            )  # system_message doesn't accept base64_image
        elif role == "assistant":
            message = Message.assistant_message(content, base64_image)
        elif role == "tool":
            message = Message.tool_message(content, base64_image=base64_image, **kwargs)

        self.memory.add_message(message)

    async def run(self, request: Optional[str] = None) -> str:
        """Execute the agent's main loop asynchronously.

        Args:
            request: Optional initial user request to process.

        Returns:
            A string summarizing the execution results.

        Raises:
            RuntimeError: If the agent is not in IDLE state at start.
        """
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Cannot run agent from state: {self.state}")

        if request:
            self.update_memory("user", request)

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while (
                self.current_step < self.max_steps and self.state != AgentState.FINISHED
            ):
                self.current_step += 1
                logger.info(f"Executing step {self.current_step}/{self.max_steps}")
                step_result = await self.step(request)

                # Check for stuck state
                if self.is_stuck():
                    self.handle_stuck_state()

                results.append(f"Step {self.current_step}: {step_result}")

            if self.current_step >= self.max_steps:
                self.current_step = 0
                self.state = AgentState.IDLE
                results.append(f"Terminated: Reached max steps ({self.max_steps})")
        # 清理sandbox（如果可用）
        if SANDBOX_CLIENT is not None:
            await SANDBOX_CLIENT.cleanup()
        return "\n".join(results) if results else "No steps executed"

    @abstractmethod
    async def step(self, content: Optional[str] = None) -> str:
        """Execute a single step in the agent's workflow.

        Args:
            content: Optional content to process in this step.

        Returns:
            str: The result of this step's execution.

        Must be implemented by subclasses to define specific behavior.
        """

    def handle_stuck_state(self):
        """Enhanced stuck state handling with strategy rotation."""
        logger.warning("Agent detected stuck state - implementing recovery strategies")

        # Reset any accumulated context that might be causing loops
        self.current_step = 0

        # List of strategy prompts to try
        strategies = [
            "Previous approach was ineffective. Try a completely different strategy.",
            "Break down the problem into smaller, more manageable steps.",
            "Consider if any assumptions being made are incorrect.",
            "Look for edge cases or exceptions that might be causing issues.",
            "Try to solve a simpler version of the problem first.",
        ]

        # Rotate through strategies based on current step
        strategy_index = (self.current_step // 2) % len(strategies)
        selected_strategy = strategies[strategy_index]

        # Update the next step prompt with the new strategy
        if self.next_step_prompt:
            self.next_step_prompt = (
                f"{selected_strategy}\n\nOriginal prompt:\n{self.next_step_prompt}"
            )
        else:
            self.next_step_prompt = selected_strategy

        # Add a system message about the strategy change
        self.update_memory(
            "system",
            f"Detected potential loop - switching to new strategy: {selected_strategy}",
        )

    def is_stuck(self) -> bool:
        """Enhanced stuck detection with content similarity and pattern recognition."""
        if (
            len(self.memory.messages) < 3
        ):  # Need at least 3 messages for pattern detection
            return False

        last_message = self.memory.messages[-1]
        if not last_message.content:
            return False

        # Get last 5 assistant messages
        recent_messages = [
            msg
            for msg in self.memory.messages[-10:]  # Look at last 10 messages
            if msg.role == "assistant" and msg.content
        ][
            -5:
        ]  # Take last 5 assistant messages

        if len(recent_messages) < 2:
            return False

        # Check for exact duplicates
        if any(msg.content == last_message.content for msg in recent_messages[:-1]):
            return True

        # Check for similar patterns (e.g. same starting phrases)
        pattern_count = 0
        for msg in recent_messages[:-1]:
            # Get first 50 chars for pattern matching
            pattern = msg.content[:50] if len(msg.content) > 50 else msg.content
            if pattern in last_message.content:
                pattern_count += 1

        # If we see similar patterns multiple times, consider it stuck
        return pattern_count >= 2

    @property
    def messages(self) -> List[Message]:
        """Retrieve a list of messages from the agent's memory."""
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        """Set the list of messages in the agent's memory."""
        self.memory.messages = value
