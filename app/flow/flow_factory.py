from enum import Enum
from typing import Dict, List, Union

from app.agent.base import BaseAgent
from app.assistants.architecture.flow import ArchitectureFlow
from app.assistants.requirements.flow import RequirementsFlow
from app.flow.base import BaseFlow
from app.flow.planning import PlanningFlow


class FlowType(str, Enum):
    PLANNING = "planning"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"


class FlowFactory:
    """Factory for creating different types of flows with support for multiple agents"""

    @staticmethod
    def create_flow(
        flow_type: FlowType,
        agents: Union[BaseAgent, List[BaseAgent], Dict[str, BaseAgent]],
        **kwargs,
    ) -> BaseFlow:
        flows = {
            FlowType.PLANNING: PlanningFlow,
            FlowType.REQUIREMENTS: RequirementsFlow,
            FlowType.ARCHITECTURE: ArchitectureFlow,
        }

        flow_class = flows.get(flow_type)
        if not flow_class:
            raise ValueError(f"Unknown flow type: {flow_type}")

        return flow_class(agents, **kwargs)
