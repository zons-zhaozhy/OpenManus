"""
Requirements analyzer tool tests
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import GlobalPromptSettings, LLMConfig, OpenManusConfig
from app.tool.requirements_analyzer import RequirementsAnalyzer


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    mock = AsyncMock()
    mock.generate.return_value = """
    Requirements Analysis:
    1. Functional Requirements:
       - User authentication
       - Data storage
       - API endpoints
    2. Non-functional Requirements:
       - Performance
       - Security
       - Scalability
    3. Technical Requirements:
       - Python 3.11+
       - PostgreSQL
       - Redis
    """
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
async def test_analyze_requirements(mock_llm, test_config):
    """Test requirements analysis"""
    analyzer = RequirementsAnalyzer(test_config)
    analyzer.llm = mock_llm

    result = await analyzer.analyze("Create a web application")
    assert "Functional Requirements" in result
    assert "Non-functional Requirements" in result
    assert "Technical Requirements" in result


@pytest.mark.asyncio
async def test_extract_requirements(mock_llm, test_config):
    """Test requirements extraction"""
    analyzer = RequirementsAnalyzer(test_config)
    analyzer.llm = mock_llm

    text = "The system should support user authentication and data storage"
    requirements = await analyzer._extract_requirements(text)
    assert isinstance(requirements, list)
    assert len(requirements) > 0


@pytest.mark.asyncio
async def test_categorize_requirements(mock_llm, test_config):
    """Test requirements categorization"""
    analyzer = RequirementsAnalyzer(test_config)
    analyzer.llm = mock_llm

    requirements = [
        "User authentication required",
        "System must be scalable",
        "Use PostgreSQL for storage",
    ]
    categories = await analyzer._categorize_requirements(requirements)
    assert isinstance(categories, dict)
    assert len(categories) > 0


@pytest.mark.asyncio
async def test_prioritize_requirements(mock_llm, test_config):
    """Test requirements prioritization"""
    analyzer = RequirementsAnalyzer(test_config)
    analyzer.llm = mock_llm

    requirements = [
        "User authentication required",
        "System must be scalable",
        "Use PostgreSQL for storage",
    ]
    priorities = await analyzer._prioritize_requirements(requirements)
    assert isinstance(priorities, dict)
    assert len(priorities) == len(requirements)


@pytest.mark.asyncio
async def test_generate_report(mock_llm, test_config):
    """Test report generation"""
    analyzer = RequirementsAnalyzer(test_config)
    analyzer.llm = mock_llm

    requirements = {
        "functional": ["User authentication", "Data storage"],
        "non_functional": ["Performance", "Security"],
        "technical": ["Python 3.11+", "PostgreSQL"],
    }
    report = await analyzer._generate_report(requirements)
    assert isinstance(report, str)
    assert "Requirements Analysis Report" in report


@pytest.mark.asyncio
async def test_error_handling(mock_llm, test_config):
    """Test error handling"""
    analyzer = RequirementsAnalyzer(test_config)
    analyzer.llm = mock_llm
    mock_llm.generate.side_effect = Exception("Analysis error")

    with pytest.raises(Exception):
        await analyzer.analyze("Create a web application")


@pytest.mark.asyncio
async def test_empty_input(mock_llm, test_config):
    """Test empty input handling"""
    analyzer = RequirementsAnalyzer(test_config)
    analyzer.llm = mock_llm

    with pytest.raises(ValueError):
        await analyzer.analyze("")


@pytest.mark.asyncio
async def test_save_report(mock_llm, test_config):
    """Test report saving"""
    analyzer = RequirementsAnalyzer(test_config)
    analyzer.llm = mock_llm

    report = "Requirements Analysis Report\n1. Requirement A\n2. Requirement B"
    await analyzer._save_report(report)

    report_files = list(
        Path(test_config.workspace_dir).glob("Requirements_Analysis_*.md")
    )
    assert len(report_files) == 1
    assert report_files[0].read_text() == report
