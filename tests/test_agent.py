"""
Manus agent tests
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.manus import Manus
from app.config import GlobalPromptSettings, LLMConfig, OpenManusConfig


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    mock = AsyncMock()
    mock.generate.return_value = "Mocked LLM response"
    return mock


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


@pytest.mark.asyncio
async def test_manus_initialization(mock_llm, test_config):
    """Test Manus agent initialization"""
    with patch("app.agent.manus.create_llm", return_value=mock_llm):
        agent = await Manus.create(test_config)
        assert agent is not None
        assert agent.config == test_config
        assert agent.analysis_progress == 0
        assert agent.analysis_metrics == {}


@pytest.mark.asyncio
async def test_analyze_requirements(mock_llm, test_config):
    """Test requirements analysis"""
    with patch("app.agent.manus.create_llm", return_value=mock_llm):
        agent = await Manus.create(test_config)
        result = await agent.analyze_requirements("Create a web application")

        assert result == "Mocked LLM response"
        assert agent.analysis_progress > 0
        assert "clarity" in agent.analysis_metrics
        assert "completeness" in agent.analysis_metrics
        assert "consistency" in agent.analysis_metrics


@pytest.mark.asyncio
async def test_progress_tracking(mock_llm, test_config):
    """Test analysis progress tracking"""
    with patch("app.agent.manus.create_llm", return_value=mock_llm):
        agent = await Manus.create(test_config)
        assert agent.get_analysis_progress() == 0

        await agent.analyze_requirements("Create a web application")
        progress = agent.get_analysis_progress()
        assert 0 <= progress <= 100


@pytest.mark.asyncio
async def test_metrics_tracking(mock_llm, test_config):
    """Test analysis metrics tracking"""
    with patch("app.agent.manus.create_llm", return_value=mock_llm):
        agent = await Manus.create(test_config)
        assert agent.get_analysis_metrics() == {}

        await agent.analyze_requirements("Create a web application")
        metrics = agent.get_analysis_metrics()
        assert all(0 <= value <= 1 for value in metrics.values())


@pytest.mark.asyncio
async def test_cleanup(mock_llm, test_config):
    """Test agent cleanup"""
    with patch("app.agent.manus.create_llm", return_value=mock_llm):
        agent = await Manus.create(test_config)
        await agent.cleanup()
        # Verify cleanup actions


@pytest.mark.asyncio
async def test_error_handling(mock_llm, test_config):
    """Test error handling during analysis"""
    mock_llm.generate.side_effect = Exception("LLM error")

    with patch("app.agent.manus.create_llm", return_value=mock_llm):
        agent = await Manus.create(test_config)
        with pytest.raises(Exception):
            await agent.analyze_requirements("Create a web application")
