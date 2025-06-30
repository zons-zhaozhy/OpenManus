"""
Bash tool tests
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tool.bash import BashTool


@pytest.fixture
def test_dir(tmp_path):
    """Create test directory structure"""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create test files
    (test_dir / "test.txt").write_text("Test content")
    (test_dir / "script.sh").write_text(
        """#!/bin/bash
echo "Hello, World!"
"""
    )

    return test_dir


@pytest.fixture
def bash_tool():
    """Create bash tool instance"""
    return BashTool()


@pytest.mark.asyncio
async def test_execute_simple_command(bash_tool):
    """Test executing a simple command"""
    result = await bash_tool.execute("echo 'Hello, World!'")
    assert result.success
    assert "Hello, World!" in result.output
    assert result.error == ""


@pytest.mark.asyncio
async def test_execute_with_error(bash_tool):
    """Test executing a command that produces an error"""
    result = await bash_tool.execute("ls nonexistent_file")
    assert not result.success
    assert "No such file or directory" in result.error


@pytest.mark.asyncio
async def test_execute_with_working_directory(bash_tool, test_dir):
    """Test executing a command in a specific working directory"""
    result = await bash_tool.execute("ls", cwd=str(test_dir))
    assert result.success
    assert "test.txt" in result.output
    assert "script.sh" in result.output


@pytest.mark.asyncio
async def test_execute_with_environment_variables(bash_tool):
    """Test executing a command with environment variables"""
    env = {"TEST_VAR": "test_value"}
    result = await bash_tool.execute("echo $TEST_VAR", env=env)
    assert result.success
    assert "test_value" in result.output


@pytest.mark.asyncio
async def test_execute_script(bash_tool, test_dir):
    """Test executing a shell script"""
    script_path = test_dir / "script.sh"
    os.chmod(script_path, 0o755)  # Make script executable

    result = await bash_tool.execute(f"bash {script_path}")
    assert result.success
    assert "Hello, World!" in result.output


@pytest.mark.asyncio
async def test_execute_with_timeout(bash_tool):
    """Test executing a command with timeout"""
    result = await bash_tool.execute("sleep 10", timeout=1)
    assert not result.success
    assert "TimeoutError" in result.error


@pytest.mark.asyncio
async def test_execute_with_input(bash_tool):
    """Test executing a command that requires input"""
    result = await bash_tool.execute('read name; echo "Hello, $name"', input="Alice\n")
    assert result.success
    assert "Hello, Alice" in result.output


@pytest.mark.asyncio
async def test_execute_with_pipe(bash_tool):
    """Test executing commands with pipe"""
    result = await bash_tool.execute("echo 'Hello' | grep 'Hello'")
    assert result.success
    assert "Hello" in result.output


@pytest.mark.asyncio
async def test_execute_with_redirection(bash_tool, test_dir):
    """Test executing commands with redirection"""
    output_file = test_dir / "output.txt"
    result = await bash_tool.execute(f"echo 'Hello' > {output_file}")
    assert result.success
    assert output_file.read_text().strip() == "Hello"


@pytest.mark.asyncio
async def test_execute_with_sudo(bash_tool):
    """Test executing commands with sudo"""
    with patch("getpass.getpass", return_value="password"):
        result = await bash_tool.execute("sudo echo 'test'", use_sudo=True)
        assert result.success or "sudo" in result.error


@pytest.mark.asyncio
async def test_execute_multiple_commands(bash_tool):
    """Test executing multiple commands"""
    result = await bash_tool.execute("mkdir test_dir && cd test_dir && pwd")
    assert result.success
    assert "test_dir" in result.output


@pytest.mark.asyncio
async def test_execute_with_wildcards(bash_tool, test_dir):
    """Test executing commands with wildcards"""
    result = await bash_tool.execute(f"ls {test_dir}/*.txt")
    assert result.success
    assert "test.txt" in result.output


@pytest.mark.asyncio
async def test_execute_with_background(bash_tool):
    """Test executing commands in background"""
    result = await bash_tool.execute("sleep 1 &")
    assert result.success
    assert "[1]" in result.output  # Job number


@pytest.mark.asyncio
async def test_execute_with_output_limit(bash_tool):
    """Test executing commands with output limit"""
    result = await bash_tool.execute("yes | head -n 1000", output_limit=100)
    assert result.success
    assert len(result.output) <= 100


@pytest.mark.asyncio
async def test_execute_with_error_handling(bash_tool):
    """Test error handling in command execution"""
    result = await bash_tool.execute("false && echo 'success' || echo 'failure'")
    assert result.success
    assert "failure" in result.output


@pytest.mark.asyncio
async def test_execute_with_path_expansion(bash_tool):
    """Test executing commands with path expansion"""
    result = await bash_tool.execute("echo ~")
    assert result.success
    assert os.path.expanduser("~") in result.output


@pytest.mark.asyncio
async def test_execute_with_quotes(bash_tool):
    """Test executing commands with quoted arguments"""
    result = await bash_tool.execute('echo "Hello   World"')
    assert result.success
    assert "Hello   World" in result.output  # Spaces preserved
