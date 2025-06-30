"""
Flow components tests
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import GlobalPromptSettings, LLMConfig, OpenManusConfig
from app.flow.base import BaseFlow
from app.flow.flow_factory import FlowFactory
from app.flow.interactive_flow import InteractiveFlow
from app.flow.planning import PlanningFlow


@pytest.fixture
def test_config(tmp_path):
    """Test configuration"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    return OpenManusConfig(
        workspace_dir=str(workspace),
        llm_config=LLMConfig(provider="openai", model="gpt-4", api_key="test_key"),
        prompt_settings=GlobalPromptSettings(
            meta_prompt="Test meta prompt", language_preference="en"
        ),
    )


class TestFlow(BaseFlow):
    """Test flow implementation"""

    async def execute(self):
        return "Test flow executed"


@pytest.mark.asyncio
async def test_base_flow():
    """Test base flow"""
    flow = TestFlow()
    result = await flow.execute()
    assert result == "Test flow executed"


@pytest.mark.asyncio
async def test_interactive_flow(test_config):
    """Test interactive flow"""
    flow = InteractiveFlow(test_config)

    # Mock user input
    with patch("builtins.input", side_effect=["Test input", "exit"]):
        with patch("builtins.print") as mock_print:
            await flow.execute()
            mock_print.assert_called()


@pytest.mark.asyncio
async def test_planning_flow(test_config):
    """Test planning flow"""
    flow = PlanningFlow(test_config)
    flow.llm = AsyncMock()
    flow.llm.generate.return_value = """
    Plan:
    1. Analyze requirements
    2. Design architecture
    3. Implement features
    """

    result = await flow.execute("Create a web application")
    assert isinstance(result, str)
    assert "Plan" in result


def test_flow_factory():
    """Test flow factory"""
    factory = FlowFactory()

    # Test interactive flow creation
    interactive_flow = factory.create_flow("interactive", test_config)
    assert isinstance(interactive_flow, InteractiveFlow)

    # Test planning flow creation
    planning_flow = factory.create_flow("planning", test_config)
    assert isinstance(planning_flow, PlanningFlow)

    # Test invalid flow type
    with pytest.raises(ValueError):
        factory.create_flow("invalid", test_config)


@pytest.mark.asyncio
async def test_flow_error_handling(test_config):
    """Test flow error handling"""
    flow = PlanningFlow(test_config)
    flow.llm = AsyncMock()
    flow.llm.generate.side_effect = Exception("Planning error")

    with pytest.raises(Exception):
        await flow.execute("Test input")


@pytest.mark.asyncio
async def test_flow_state_management(test_config):
    """Test flow state management"""
    flow = PlanningFlow(test_config)

    # Test state initialization
    assert flow.state == {}

    # Test state updates
    flow.update_state({"key": "value"})
    assert flow.state["key"] == "value"

    # Test state reset
    flow.reset_state()
    assert flow.state == {}


@pytest.mark.asyncio
async def test_flow_progress_tracking(test_config):
    """Test flow progress tracking"""
    flow = PlanningFlow(test_config)

    # Test progress initialization
    assert flow.progress == 0

    # Test progress updates
    flow.update_progress(50)
    assert flow.progress == 50

    # Test progress validation
    with pytest.raises(ValueError):
        flow.update_progress(101)  # Invalid progress value


@pytest.mark.asyncio
async def test_flow_context_management(test_config):
    """Test flow context management"""
    flow = PlanningFlow(test_config)

    # Test context initialization
    assert flow.context == {}

    # Test context updates
    flow.update_context({"key": "value"})
    assert flow.context["key"] == "value"

    # Test context reset
    flow.reset_context()
    assert flow.context == {}
