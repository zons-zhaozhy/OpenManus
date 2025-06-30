from typing import Dict, Any, Optional
from fastapi import WebSocket
from app.schema import Event, EventType
from app.assistants.requirements.agents.clarification_agent import ClarificationAgent
from app.assistants.requirements.agents.analysis_agent import AnalysisAgent
from app.assistants.requirements.agents.documentation_agent import DocumentationAgent
from app.assistants.requirements.project.services.websocket_event_publisher import WebSocketEventPublisher

class InteractiveFlowManager:
    def __init__(self, session_id: str, websocket: Optional[WebSocket] = None):
        self.session_id = session_id
        self.event_publisher = WebSocketEventPublisher({session_id: websocket}) if websocket else None
        self.clarification_agent = ClarificationAgent()
        self.analysis_agent = AnalysisAgent()
        self.documentation_agent = DocumentationAgent()
        self.state = {"stage": "initial", "data": {}}

    async def start(self):
        """Start the interactive flow for requirements analysis."""
        await self._publish_event(EventType.TASK_START, "Starting requirements analysis flow")
        self.state["stage"] = "clarification"
        await self._run_clarification()

    async def handle_input(self, user_input: str):
        """Handle user input based on the current stage of the flow."""
        if self.state["stage"] == "clarification":
            await self._process_clarification_input(user_input)
        elif self.state["stage"] == "analysis":
            await self._process_analysis_input(user_input)
        elif self.state["stage"] == "documentation":
            await self._process_documentation_input(user_input)

    async def _publish_event(self, event_type: EventType, data: Any):
        """Publish an event to the connected client if a publisher is set."""
        if self.event_publisher:
            event = Event(type=event_type, data=data)
            await self.event_publisher.publish_custom_event(self.session_id, event_type.value, {"type": event_type.value, "data": data})

    async def _run_clarification(self):
        """Run the clarification stage of the flow."""
        await self._publish_event(EventType.STAGE_CHANGE, "Entering Clarification Stage")
        clarification_result = await self.clarification_agent.process_input("")
        self.state["data"]["clarification"] = clarification_result
        await self._publish_event(EventType.LOG, f"Clarification result: {clarification_result}")
        if clarification_result.get("status") == "complete":
            self.state["stage"] = "analysis"
            await self._run_analysis()

    async def _run_analysis(self):
        """Run the analysis stage of the flow."""
        await self._publish_event(EventType.STAGE_CHANGE, "Entering Analysis Stage")
        clarification_data = self.state["data"].get("clarification", {})
        analysis_result = await self.analysis_agent.analyze(clarification_data)
        self.state["data"]["analysis"] = analysis_result
        await self._publish_event(EventType.LOG, f"Analysis result: {analysis_result}")
        if analysis_result.get("status") == "complete":
            self.state["stage"] = "documentation"
            await self._run_documentation()

    async def _run_documentation(self):
        """Run the documentation stage of the flow."""
        await self._publish_event(EventType.STAGE_CHANGE, "Entering Documentation Stage")
        analysis_data = self.state["data"].get("analysis", {})
        documentation_result = await self.documentation_agent.generate_documentation(analysis_data)
        self.state["data"]["documentation"] = documentation_result
        await self._publish_event(EventType.LOG, f"Documentation result: {documentation_result}")
        if documentation_result.get("status") == "complete":
            self.state["stage"] = "complete"
            await self._publish_event(EventType.TASK_COMPLETE, "Requirements analysis completed")

    async def _process_clarification_input(self, user_input: str):
        """Process user input during the clarification stage."""
        await self._publish_event(EventType.LOG, f"Received user input for clarification: {user_input}")
        clarification_result = await self.clarification_agent.process_input(user_input)
        self.state["data"]["clarification"] = clarification_result
        await self._publish_event(EventType.LOG, f"Updated clarification result: {clarification_result}")
        if clarification_result.get("status") == "complete":
            self.state["stage"] = "analysis"
            await self._run_analysis()

    async def _process_analysis_input(self, user_input: str):
        """Process user input during the analysis stage."""
        await self._publish_event(EventType.LOG, f"Received user input for analysis: {user_input}")
        analysis_result = await self.analysis_agent.process_input(user_input, self.state["data"].get("clarification", {}))
        self.state["data"]["analysis"] = analysis_result
        await self._publish_event(EventType.LOG, f"Updated analysis result: {analysis_result}")
        if analysis_result.get("status") == "complete":
            self.state["stage"] = "documentation"
            await self._run_documentation()

    async def _process_documentation_input(self, user_input: str):
        """Process user input during the documentation stage."""
        await self._publish_event(EventType.LOG, f"Received user input for documentation: {user_input}")
        documentation_result = await self.documentation_agent.process_input(user_input, self.state["data"].get("analysis", {}))
        self.state["data"]["documentation"] = documentation_result
        await self._publish_event(EventType.LOG, f"Updated documentation result: {documentation_result}")
        if documentation_result.get("status") == "complete":
            self.state["stage"] = "complete"
            await self._publish_event(EventType.TASK_COMPLETE, "Requirements analysis completed")
