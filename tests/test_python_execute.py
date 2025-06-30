"""
Python execute tests
"""

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.tool.python_execute import PythonExecutor


@pytest.fixture
def executor():
    """Create Python executor instance"""
    return PythonExecutor()


@pytest.fixture
def test_dir(tmp_path):
    """Create test directory structure"""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create test files
    (test_dir / "test_script.py").write_text(
        """
def add(a, b):
    return a + b

result = add(2, 3)
print(f"Result: {result}")
"""
    )

    (test_dir / "error_script.py").write_text(
        """
def divide(a, b):
    return a / b

result = divide(10, 0)  # Division by zero error
"""
    )

    (test_dir / "input_script.py").write_text(
        """
name = input("Enter your name: ")
print(f"Hello, {name}!")
"""
    )

    return test_dir


def test_execute_simple_script(executor, test_dir):
    """Test executing a simple script"""
    script_path = test_dir / "test_script.py"

    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        result = executor.execute(str(script_path))
        assert result.success
        assert "Result: 5" in fake_output.getvalue()
        assert result.error is None


def test_execute_with_error(executor, test_dir):
    """Test executing a script with an error"""
    script_path = test_dir / "error_script.py"

    result = executor.execute(str(script_path))
    assert not result.success
    assert "ZeroDivisionError" in result.error
    assert "division by zero" in result.error


def test_execute_with_input(executor, test_dir):
    """Test executing a script that requires input"""
    script_path = test_dir / "input_script.py"
    test_input = "Alice"

    with patch("builtins.input", return_value=test_input), patch(
        "sys.stdout", new=io.StringIO()
    ) as fake_output:
        result = executor.execute(str(script_path))
        assert result.success
        assert f"Hello, {test_input}!" in fake_output.getvalue()


def test_execute_nonexistent_file(executor, test_dir):
    """Test executing a non-existent file"""
    script_path = test_dir / "nonexistent.py"

    result = executor.execute(str(script_path))
    assert not result.success
    assert "FileNotFoundError" in result.error


def test_execute_with_syntax_error(executor, test_dir):
    """Test executing a script with syntax error"""
    script_path = test_dir / "syntax_error.py"
    script_path.write_text("print('Unclosed string)")

    result = executor.execute(str(script_path))
    assert not result.success
    assert "SyntaxError" in result.error


def test_execute_with_timeout(executor, test_dir):
    """Test executing a script that times out"""
    script_path = test_dir / "timeout_script.py"
    script_path.write_text(
        """
import time
while True:
    time.sleep(1)
"""
    )

    result = executor.execute(str(script_path), timeout=2)
    assert not result.success
    assert "TimeoutError" in result.error


def test_execute_with_imports(executor, test_dir):
    """Test executing a script with imports"""
    script_path = test_dir / "import_script.py"
    script_path.write_text(
        """
import math
print(f"Pi: {math.pi}")
"""
    )

    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        result = executor.execute(str(script_path))
        assert result.success
        assert "Pi: 3.14" in fake_output.getvalue()


def test_execute_with_arguments(executor, test_dir):
    """Test executing a script with command line arguments"""
    script_path = test_dir / "args_script.py"
    script_path.write_text(
        """
import sys
print(f"Arguments: {sys.argv[1:]}")
"""
    )

    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        result = executor.execute(str(script_path), args=["arg1", "arg2"])
        assert result.success
        assert "Arguments: ['arg1', 'arg2']" in fake_output.getvalue()


def test_execute_with_environment_variables(executor, test_dir):
    """Test executing a script with environment variables"""
    script_path = test_dir / "env_script.py"
    script_path.write_text(
        """
import os
print(f"TEST_VAR: {os.getenv('TEST_VAR')}")
"""
    )

    with patch("sys.stdout", new=io.StringIO()) as fake_output, patch.dict(
        "os.environ", {"TEST_VAR": "test_value"}
    ):
        result = executor.execute(str(script_path))
        assert result.success
        assert "TEST_VAR: test_value" in fake_output.getvalue()


def test_execute_with_working_directory(executor, test_dir):
    """Test executing a script with a specific working directory"""
    script_path = test_dir / "cwd_script.py"
    script_path.write_text(
        """
import os
print(f"CWD: {os.getcwd()}")
"""
    )

    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        result = executor.execute(str(script_path), cwd=str(test_dir))
        assert result.success
        assert str(test_dir) in fake_output.getvalue()


def test_execute_with_memory_limit(executor, test_dir):
    """Test executing a script with memory limit"""
    script_path = test_dir / "memory_script.py"
    script_path.write_text(
        """
data = [0] * (1024 * 1024 * 100)  # Allocate ~800MB
"""
    )

    result = executor.execute(str(script_path), memory_limit=50)  # 50MB limit
    assert not result.success
    assert "MemoryError" in result.error


def test_execute_with_output_limit(executor, test_dir):
    """Test executing a script with output limit"""
    script_path = test_dir / "output_script.py"
    script_path.write_text(
        """
for i in range(1000000):
    print(f"Line {i}")
"""
    )

    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        result = executor.execute(str(script_path), output_limit=1000)
        assert result.success
        assert len(fake_output.getvalue()) <= 1000


def test_execute_with_restricted_imports(executor, test_dir):
    """Test executing a script with restricted imports"""
    script_path = test_dir / "restricted_script.py"
    script_path.write_text(
        """
import os
os.system('echo "test"')
"""
    )

    result = executor.execute(str(script_path), restricted=True)
    assert not result.success
    assert "ImportError" in result.error or "SecurityError" in result.error


def test_execute_concurrent_scripts(executor, test_dir):
    """Test executing multiple scripts concurrently"""
    script_paths = []
    for i in range(3):
        path = test_dir / f"concurrent_{i}.py"
        path.write_text(f"print('Script {i}')")
        script_paths.append(str(path))

    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        results = executor.execute_concurrent(script_paths)
        assert all(result.success for result in results)
        output = fake_output.getvalue()
        assert all(f"Script {i}" in output for i in range(3))
