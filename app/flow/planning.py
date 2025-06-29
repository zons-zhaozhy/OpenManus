import json
import time
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import Field

from app.agent.base import BaseAgent
from app.config.timeouts import TimeoutConfig, get_timeout_config
from app.flow.base import BaseFlow
from app.flow.state import FlowState, FlowStateManager
from app.llm import LLM
from app.logger import logger
from app.schema import AgentState, Message, ToolChoice
from app.tool import PlanningTool


class PlanStepStatus(str, Enum):
    """Enum class defining possible statuses of a plan step"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

    @classmethod
    def get_all_statuses(cls) -> list[str]:
        """Return a list of all possible step status values"""
        return [status.value for status in cls]

    @classmethod
    def get_active_statuses(cls) -> list[str]:
        """Return a list of values representing active statuses (not started or in progress)"""
        return [cls.NOT_STARTED.value, cls.IN_PROGRESS.value]

    @classmethod
    def get_status_marks(cls) -> Dict[str, str]:
        """Return a mapping of statuses to their marker symbols"""
        return {
            cls.COMPLETED.value: "[✓]",
            cls.IN_PROGRESS.value: "[→]",
            cls.BLOCKED.value: "[!]",
            cls.NOT_STARTED.value: "[ ]",
        }


class PlanningFlow(BaseFlow):
    """A flow that manages planning and execution of tasks using agents."""

    llm: LLM = Field(default_factory=lambda: LLM())
    planning_tool: PlanningTool = Field(default_factory=PlanningTool)
    executor_keys: List[str] = Field(default_factory=list)
    active_plan_id: str = Field(default_factory=lambda: f"plan_{int(time.time())}")
    current_step_index: Optional[int] = None
    timeout_config: TimeoutConfig = Field(
        default_factory=lambda: get_timeout_config("planning")
    )
    current_attempt: int = Field(default=1)
    state_manager: FlowStateManager = Field(default_factory=FlowStateManager)

    def __init__(
        self, agents: Union[BaseAgent, List[BaseAgent], Dict[str, BaseAgent]], **data
    ):
        # Initialize timeout config if provided
        if "timeout_config" in data:
            data["timeout_config"] = TimeoutConfig(**data["timeout_config"])

        # Initialize state manager if provided
        if "state_manager" in data:
            data["state_manager"] = FlowStateManager(**data["state_manager"])

        # Set executor keys before super().__init__
        if "executors" in data:
            data["executor_keys"] = data.pop("executors")

        # Set plan ID if provided
        if "plan_id" in data:
            data["active_plan_id"] = data.pop("plan_id")

        # Initialize the planning tool if not provided
        if "planning_tool" not in data:
            planning_tool = PlanningTool()
            data["planning_tool"] = planning_tool

        # Call parent's init with the processed data
        super().__init__(agents, **data)

        # Set executor_keys to all agent keys if not specified
        if not self.executor_keys:
            self.executor_keys = list(self.agents.keys())

    def get_executor(self, step_type: Optional[str] = None) -> BaseAgent:
        """
        Get an appropriate executor agent for the current step with enhanced selection logic.

        Args:
            step_type: Optional type of step to execute

        Returns:
            BaseAgent: The most appropriate agent for executing the step

        Raises:
            ValueError: If no suitable agent can be found
        """
        # Track agent selection reason for logging
        selection_reason = "default selection"
        selected_agent = None

        try:
            # Case 1: Step type matches an agent key exactly
            if step_type and step_type in self.agents:
                selected_agent = self.agents[step_type]
                selection_reason = f"exact match for step type: {step_type}"

            # Case 2: Step type matches part of an agent key
            elif step_type:
                for key, agent in self.agents.items():
                    if step_type.lower() in key.lower():
                        selected_agent = agent
                        selection_reason = f"partial match: {step_type} in {key}"
                        break

            # Case 3: Use executor_keys in priority order
            if not selected_agent:
                for key in self.executor_keys:
                    if key in self.agents:
                        selected_agent = self.agents[key]
                        selection_reason = f"found in executor_keys: {key}"
                        break

            # Case 4: Fallback to primary agent
            if not selected_agent and self.primary_agent:
                selected_agent = self.primary_agent
                selection_reason = "fallback to primary agent"

            # Case 5: Last resort - use first available agent
            if not selected_agent and self.agents:
                key = next(iter(self.agents))
                selected_agent = self.agents[key]
                selection_reason = f"last resort selection: {key}"

            # If we still don't have an agent, raise an error
            if not selected_agent:
                raise ValueError("No suitable agent found for execution")

            # Log the selection
            logger.info(f"Selected agent: {selected_agent.name} ({selection_reason})")

            return selected_agent

        except Exception as e:
            logger.error(f"Error selecting executor: {str(e)}")
            raise ValueError(f"Failed to select executor: {str(e)}")

    async def execute(self, input_text: str) -> str:
        """Execute the planning flow with agents."""
        try:
            if not self.primary_agent:
                raise ValueError("No primary agent available")

            # Initialize flow state
            self.state_manager.transition_to(FlowState.RUNNING.value)
            self.state_manager.update_data("start_time", time.time())

            # Create initial plan if input provided
            if input_text:
                await self._create_initial_plan(input_text)

                # Verify plan was created successfully
                if self.active_plan_id not in self.planning_tool.plans:
                    error_msg = f"Plan creation failed. Plan ID {self.active_plan_id} not found in planning tool."
                    self.state_manager.record_error(error_msg)
                    return f"Failed to create plan for: {input_text}"

            result = ""
            iteration_count = 0

            while (
                iteration_count < self.timeout_config.max_iterations
                and self.state_manager.can_proceed()
            ):
                iteration_count += 1

                # Check total execution time
                elapsed_time = time.time() - self.state_manager.get_data(
                    "start_time", 0
                )
                if elapsed_time > self.timeout_config.total_timeout:
                    logger.warning("Planning flow execution approaching timeout limit")
                    result += "\n[System] Execution approaching timeout limit - finalizing current progress."
                    break

                # Get current step to execute
                self.current_step_index, step_info = await self._get_current_step_info()

                # Exit if no more steps or plan completed
                if self.current_step_index is None:
                    self.state_manager.transition_to(FlowState.COMPLETED.value)
                    result += await self._finalize_plan()
                    break

                # Log progress
                logger.info(
                    f"Executing step {iteration_count}/{self.timeout_config.max_iterations} "
                    f"(elapsed: {elapsed_time:.1f}s)"
                )

                # Execute current step with appropriate agent
                step_type = step_info.get("type") if step_info else None
                executor = self.get_executor(step_type)

                # Reset attempt counter for new step
                self.current_attempt = 1

                while (
                    self.current_attempt <= self.timeout_config.max_retries
                    and self.state_manager.can_proceed()
                ):
                    try:
                        step_result = await self._execute_step(executor, step_info)
                        result += step_result + "\n"
                        self.state_manager.reset_errors()  # Reset error count on success
                        break
                    except Exception as e:
                        error_msg = f"Step execution failed (attempt {self.current_attempt}): {str(e)}"
                        if self.state_manager.record_error(error_msg):
                            # Max errors exceeded
                            logger.error(
                                f"Step execution failed after {self.current_attempt} attempts"
                            )
                            result += f"Step execution failed: {str(e)}\n"
                            # Update step status to blocked
                            if self.current_step_index is not None:
                                self.planning_tool.update_step_status(
                                    self.active_plan_id,
                                    self.current_step_index,
                                    PlanStepStatus.BLOCKED.value,
                                )
                            break
                        else:
                            logger.warning(
                                f"Retrying step execution (attempt {self.current_attempt + 1})"
                            )
                            await asyncio.sleep(self.timeout_config.retry_delay)
                            self.current_attempt += 1
                            continue

                # Check if agent wants to terminate
                if hasattr(executor, "state") and executor.state == AgentState.FINISHED:
                    self.state_manager.transition_to(FlowState.COMPLETED.value)
                    break

            # Handle max iterations reached
            if iteration_count >= self.timeout_config.max_iterations:
                logger.warning(
                    f"⚠️ PlanningFlow reached max iterations ({self.timeout_config.max_iterations})"
                )
                result += "\n[System] Execution reached maximum steps - finalizing current progress."

                # Try to gracefully finish the plan
                result += await self._finalize_plan()

            # Add final state information
            if self.state_manager.is_terminal():
                result += f"\n[System] Flow completed in state: {self.state_manager.current_state}"
                if self.state_manager.last_error:
                    result += f"\nLast error: {self.state_manager.last_error}"

            return result
        except Exception as e:
            error_msg = f"Error in PlanningFlow: {str(e)}"
            logger.error(error_msg)
            self.state_manager.record_error(error_msg)
            return f"Execution failed: {str(e)}"

    async def _create_initial_plan(self, request: str) -> None:
        """Create an initial plan based on the request using the flow's LLM and PlanningTool."""
        logger.info(f"Creating initial plan with ID: {self.active_plan_id}")

        system_message_content = (
            "You are a planning assistant. Create a concise, actionable plan with clear steps. "
            "Focus on key milestones rather than detailed sub-steps. "
            "Optimize for clarity and efficiency."
        )
        agents_description = []
        for key in self.executor_keys:
            if key in self.agents:
                agents_description.append(
                    {
                        "name": key.upper(),
                        "description": self.agents[key].description,
                    }
                )
        if len(agents_description) > 1:
            # Add description of agents to select
            system_message_content += (
                f"\nNow we have {agents_description} agents. "
                f"The infomation of them are below: {json.dumps(agents_description)}\n"
                "When creating steps in the planning tool, please specify the agent names using the format '[agent_name]'."
            )

        # Create a system message for plan creation
        system_message = Message.system_message(system_message_content)

        # Create a user message with the request
        user_message = Message.user_message(
            f"Create a reasonable plan with clear steps to accomplish the task: {request}"
        )

        # Call LLM with PlanningTool
        response = await self.llm.ask_tool(
            messages=[user_message],
            system_msgs=[system_message],
            tools=[self.planning_tool.to_param()],
            tool_choice=ToolChoice.AUTO,
        )

        # Process tool calls if present
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.function.name == "planning":
                    # Parse the arguments
                    args = tool_call.function.arguments
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse tool arguments: {args}")
                            continue

                    # Ensure plan_id is set correctly and execute the tool
                    args["plan_id"] = self.active_plan_id

                    # Execute the tool via ToolCollection instead of directly
                    result = await self.planning_tool.execute(**args)

                    logger.info(f"Plan creation result: {str(result)}")
                    return

        # If execution reached here, create a default plan
        logger.warning("Creating default plan")

        # Create default plan using the ToolCollection
        await self.planning_tool.execute(
            **{
                "command": "create",
                "plan_id": self.active_plan_id,
                "title": f"Plan for: {request[:50]}{'...' if len(request) > 50 else ''}",
                "steps": ["Analyze request", "Execute task", "Verify results"],
            }
        )

    async def _get_current_step_info(self) -> tuple[Optional[int], Optional[dict]]:
        """
        Parse the current plan to identify the first non-completed step's index and info.
        Returns (None, None) if no active step is found.
        """
        if (
            not self.active_plan_id
            or self.active_plan_id not in self.planning_tool.plans
        ):
            logger.error(f"Plan with ID {self.active_plan_id} not found")
            return None, None

        try:
            # Direct access to plan data from planning tool storage
            plan_data = self.planning_tool.plans[self.active_plan_id]
            steps = plan_data.get("steps", [])
            step_statuses = plan_data.get("step_statuses", [])

            # Find first non-completed step
            for i, step in enumerate(steps):
                if i >= len(step_statuses):
                    status = PlanStepStatus.NOT_STARTED.value
                else:
                    status = step_statuses[i]

                if status in PlanStepStatus.get_active_statuses():
                    # Extract step type/category if available
                    step_info = {"text": step}

                    # Try to extract step type from the text (e.g., [SEARCH] or [CODE])
                    import re

                    type_match = re.search(r"\[([A-Z_]+)\]", step)
                    if type_match:
                        step_info["type"] = type_match.group(1).lower()

                    # Mark current step as in_progress
                    try:
                        await self.planning_tool.execute(
                            command="mark_step",
                            plan_id=self.active_plan_id,
                            step_index=i,
                            step_status=PlanStepStatus.IN_PROGRESS.value,
                        )
                    except Exception as e:
                        logger.warning(f"Error marking step as in_progress: {e}")
                        # Update step status directly if needed
                        if i < len(step_statuses):
                            step_statuses[i] = PlanStepStatus.IN_PROGRESS.value
                        else:
                            while len(step_statuses) < i:
                                step_statuses.append(PlanStepStatus.NOT_STARTED.value)
                            step_statuses.append(PlanStepStatus.IN_PROGRESS.value)

                        plan_data["step_statuses"] = step_statuses

                    return i, step_info

            return None, None  # No active step found

        except Exception as e:
            logger.warning(f"Error finding current step index: {e}")
            return None, None

    async def _execute_step(self, executor: BaseAgent, step_info: dict) -> str:
        """Execute a single step with timeout and error handling."""
        import asyncio
        from asyncio import TimeoutError

        try:
            # Get progressive timeout based on current attempt
            step_timeout = self.timeout_config.get_step_timeout(self.current_attempt)

            # Set a timeout for step execution
            async with asyncio.timeout(step_timeout):
                # Get step content
                step_content = step_info.get("content", "")
                if not step_content:
                    logger.warning("Empty step content received")
                    return "Step skipped - no content"

                # Execute step with executor
                result = await executor.run(step_content)

                # Mark step as completed if successful
                await self._mark_step_completed()

                return result

        except TimeoutError:
            logger.error(f"Step execution timed out after {step_timeout} seconds")
            raise  # Let the retry logic in execute() handle it

        except Exception as e:
            logger.error(f"Error executing step: {str(e)}")
            raise  # Let the retry logic in execute() handle it

    async def _mark_step_completed(self) -> None:
        """Mark the current step as completed."""
        if self.current_step_index is None:
            return

        try:
            # Mark the step as completed
            await self.planning_tool.execute(
                command="mark_step",
                plan_id=self.active_plan_id,
                step_index=self.current_step_index,
                step_status=PlanStepStatus.COMPLETED.value,
            )
            logger.info(
                f"Marked step {self.current_step_index} as completed in plan {self.active_plan_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to update plan status: {e}")
            # Update step status directly in planning tool storage
            if self.active_plan_id in self.planning_tool.plans:
                plan_data = self.planning_tool.plans[self.active_plan_id]
                step_statuses = plan_data.get("step_statuses", [])

                # Ensure the step_statuses list is long enough
                while len(step_statuses) <= self.current_step_index:
                    step_statuses.append(PlanStepStatus.NOT_STARTED.value)

                # Update the status
                step_statuses[self.current_step_index] = PlanStepStatus.COMPLETED.value
                plan_data["step_statuses"] = step_statuses

    async def _get_plan_text(self) -> str:
        """Get the current plan as formatted text."""
        try:
            result = await self.planning_tool.execute(
                command="get", plan_id=self.active_plan_id
            )
            return result.output if hasattr(result, "output") else str(result)
        except Exception as e:
            logger.error(f"Error getting plan: {e}")
            return self._generate_plan_text_from_storage()

    def _generate_plan_text_from_storage(self) -> str:
        """Generate plan text directly from storage if the planning tool fails."""
        try:
            if self.active_plan_id not in self.planning_tool.plans:
                return f"Error: Plan with ID {self.active_plan_id} not found"

            plan_data = self.planning_tool.plans[self.active_plan_id]
            title = plan_data.get("title", "Untitled Plan")
            steps = plan_data.get("steps", [])
            step_statuses = plan_data.get("step_statuses", [])
            step_notes = plan_data.get("step_notes", [])

            # Ensure step_statuses and step_notes match the number of steps
            while len(step_statuses) < len(steps):
                step_statuses.append(PlanStepStatus.NOT_STARTED.value)
            while len(step_notes) < len(steps):
                step_notes.append("")

            # Count steps by status
            status_counts = {status: 0 for status in PlanStepStatus.get_all_statuses()}

            for status in step_statuses:
                if status in status_counts:
                    status_counts[status] += 1

            completed = status_counts[PlanStepStatus.COMPLETED.value]
            total = len(steps)
            progress = (completed / total) * 100 if total > 0 else 0

            plan_text = f"Plan: {title} (ID: {self.active_plan_id})\n"
            plan_text += "=" * len(plan_text) + "\n\n"

            plan_text += (
                f"Progress: {completed}/{total} steps completed ({progress:.1f}%)\n"
            )
            plan_text += f"Status: {status_counts[PlanStepStatus.COMPLETED.value]} completed, {status_counts[PlanStepStatus.IN_PROGRESS.value]} in progress, "
            plan_text += f"{status_counts[PlanStepStatus.BLOCKED.value]} blocked, {status_counts[PlanStepStatus.NOT_STARTED.value]} not started\n\n"
            plan_text += "Steps:\n"

            status_marks = PlanStepStatus.get_status_marks()

            for i, (step, status, notes) in enumerate(
                zip(steps, step_statuses, step_notes)
            ):
                # Use status marks to indicate step status
                status_mark = status_marks.get(
                    status, status_marks[PlanStepStatus.NOT_STARTED.value]
                )

                plan_text += f"{i}. {status_mark} {step}\n"
                if notes:
                    plan_text += f"   Notes: {notes}\n"

            return plan_text
        except Exception as e:
            logger.error(f"Error generating plan text from storage: {e}")
            return f"Error: Unable to retrieve plan with ID {self.active_plan_id}"

    async def _finalize_plan(self) -> str:
        """Finalize the plan and provide a summary using the flow's LLM directly."""
        plan_text = await self._get_plan_text()

        # Create a summary using the flow's LLM directly
        try:
            system_message = Message.system_message(
                "You are a planning assistant. Your task is to summarize the completed plan."
            )

            user_message = Message.user_message(
                f"The plan has been completed. Here is the final plan status:\n\n{plan_text}\n\nPlease provide a summary of what was accomplished and any final thoughts."
            )

            response = await self.llm.ask(
                messages=[user_message], system_msgs=[system_message]
            )

            return f"Plan completed:\n\n{response}"
        except Exception as e:
            logger.error(f"Error finalizing plan with LLM: {e}")

            # Fallback to using an agent for the summary
            try:
                agent = self.primary_agent
                summary_prompt = f"""
                The plan has been completed. Here is the final plan status:

                {plan_text}

                Please provide a summary of what was accomplished and any final thoughts.
                """
                summary = await agent.run(summary_prompt)
                return f"Plan completed:\n\n{summary}"
            except Exception as e2:
                logger.error(f"Error finalizing plan with agent: {e2}")
                return "Plan completed. Error generating summary."
