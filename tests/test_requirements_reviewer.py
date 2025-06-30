"""
Requirements reviewer tool tests
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import GlobalPromptSettings, LLMConfig, OpenManusConfig
from app.tool.requirements_reviewer import RequirementsReviewer


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    mock = AsyncMock()
    mock.generate.return_value = """
    Requirements Review:
    1. Completeness: 85%
       - All core features covered
       - Some edge cases missing
    2. Clarity: 90%
       - Requirements well-defined
       - Clear acceptance criteria
    3. Consistency: 95%
       - No conflicting requirements
       - Terminology consistent
    4. Feasibility: 80%
       - Technical stack viable
       - Some performance concerns
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
async def test_review_requirements(mock_llm, test_config):
    """Test requirements review"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm

    requirements = """
    1. User authentication with OAuth
    2. Real-time data synchronization
    3. Automated backup system
    """

    result = await reviewer.review(requirements)
    assert "Completeness" in result
    assert "Clarity" in result
    assert "Consistency" in result
    assert "Feasibility" in result


@pytest.mark.asyncio
async def test_analyze_completeness(mock_llm, test_config):
    """Test completeness analysis"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm

    requirements = ["User authentication", "Data storage"]
    score, feedback = await reviewer._analyze_completeness(requirements)
    assert isinstance(score, float)
    assert 0 <= score <= 1
    assert isinstance(feedback, str)


@pytest.mark.asyncio
async def test_analyze_clarity(mock_llm, test_config):
    """Test clarity analysis"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm

    requirements = [
        "System must respond within 200ms",
        "Data must be encrypted at rest",
    ]
    score, feedback = await reviewer._analyze_clarity(requirements)
    assert isinstance(score, float)
    assert 0 <= score <= 1
    assert isinstance(feedback, str)


@pytest.mark.asyncio
async def test_analyze_consistency(mock_llm, test_config):
    """Test consistency analysis"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm

    requirements = ["Use PostgreSQL for data storage", "Store data in MySQL database"]
    score, feedback = await reviewer._analyze_consistency(requirements)
    assert isinstance(score, float)
    assert 0 <= score <= 1
    assert isinstance(feedback, str)


@pytest.mark.asyncio
async def test_analyze_feasibility(mock_llm, test_config):
    """Test feasibility analysis"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm

    requirements = ["Process 1 million requests per second", "Achieve 100% uptime"]
    score, feedback = await reviewer._analyze_feasibility(requirements)
    assert isinstance(score, float)
    assert 0 <= score <= 1
    assert isinstance(feedback, str)


@pytest.mark.asyncio
async def test_generate_report(mock_llm, test_config):
    """Test report generation"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm

    analysis = {
        "completeness": (0.85, "All core features covered"),
        "clarity": (0.90, "Requirements well-defined"),
        "consistency": (0.95, "No conflicts found"),
        "feasibility": (0.80, "Technical stack viable"),
    }

    report = await reviewer._generate_report(analysis)
    assert isinstance(report, str)
    assert "Requirements Review Report" in report


@pytest.mark.asyncio
async def test_error_handling(mock_llm, test_config):
    """Test error handling"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm
    mock_llm.generate.side_effect = Exception("Review error")

    with pytest.raises(Exception):
        await reviewer.review("Test requirements")


@pytest.mark.asyncio
async def test_empty_input(mock_llm, test_config):
    """Test empty input handling"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm

    with pytest.raises(ValueError):
        await reviewer.review("")


@pytest.mark.asyncio
async def test_save_review(mock_llm, test_config):
    """Test review saving"""
    reviewer = RequirementsReviewer(test_config)
    reviewer.llm = mock_llm

    review = "Requirements Review Report\n1. Completeness: 85%\n2. Clarity: 90%"
    await reviewer._save_review(review)

    review_files = list(
        Path(test_config.workspace_dir).glob("Requirements_Review_*.md")
    )
    assert len(review_files) == 1
    assert review_files[0].read_text() == review
