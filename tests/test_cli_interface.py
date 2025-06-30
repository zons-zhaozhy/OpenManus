"""
CLI interface tests
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.interfaces.cli_interface import CLIInterface


@pytest.fixture
def mock_agent():
    """Mock Manus agent for testing"""
    mock = AsyncMock()
    mock.analyze_requirements.return_value = "Analysis result"
    mock.get_analysis_progress.return_value = 50
    mock.get_analysis_metrics.return_value = {
        "clarity": 0.8,
        "completeness": 0.7,
        "consistency": 0.9,
    }
    return mock


@pytest.fixture
def cli_interface():
    """Create CLI interface instance"""
    return CLIInterface()


@pytest.mark.asyncio
async def test_question_parsing():
    """Test question parsing"""
    interface = CLIInterface()
    question = "Create a web application"
    parsed = interface._parse_question(question)
    assert parsed == question


@pytest.mark.asyncio
async def test_format_response():
    """Test response formatting"""
    interface = CLIInterface()
    response = "Analysis result with multiple\nlines of text"
    formatted = interface._format_response(response)
    assert isinstance(formatted, str)
    assert "Analysis result" in formatted


@pytest.mark.asyncio
async def test_interactive_mode(mock_agent):
    """Test interactive mode"""
    interface = CLIInterface()

    with patch("builtins.input", side_effect=["Create a web application", "exit"]):
        with patch("builtins.print") as mock_print:
            await interface.run(mock_agent)
            mock_agent.analyze_requirements.assert_called_once()
            mock_print.assert_called()


@pytest.mark.asyncio
async def test_progress_display(mock_agent):
    """Test progress display"""
    interface = CLIInterface()

    with patch("builtins.print") as mock_print:
        interface._display_progress(50)
        mock_print.assert_called()


@pytest.mark.asyncio
async def test_metrics_display(mock_agent):
    """Test metrics display"""
    interface = CLIInterface()
    metrics = {"clarity": 0.8, "completeness": 0.7, "consistency": 0.9}

    with patch("builtins.print") as mock_print:
        interface._display_metrics(metrics)
        mock_print.assert_called()


@pytest.mark.asyncio
async def test_error_handling(mock_agent):
    """Test error handling"""
    interface = CLIInterface()
    mock_agent.analyze_requirements.side_effect = Exception("Analysis error")

    with patch("builtins.input", return_value="Create a web application"):
        with patch("builtins.print") as mock_print:
            await interface.run(mock_agent)
            mock_print.assert_called()


@pytest.mark.asyncio
async def test_exit_command():
    """Test exit command handling"""
    interface = CLIInterface()

    with patch("builtins.input", return_value="exit"):
        with patch("builtins.print") as mock_print:
            await interface.run(AsyncMock())
            mock_print.assert_called()


@pytest.mark.asyncio
async def test_help_command():
    """Test help command"""
    interface = CLIInterface()

    with patch("builtins.input", side_effect=["help", "exit"]):
        with patch("builtins.print") as mock_print:
            await interface.run(AsyncMock())
            mock_print.assert_called()


@pytest.mark.asyncio
async def test_clear_command():
    """Test clear command"""
    interface = CLIInterface()

    with patch("builtins.input", side_effect=["clear", "exit"]):
        with patch("os.system") as mock_system:
            await interface.run(AsyncMock())
            mock_system.assert_called_with("clear")
