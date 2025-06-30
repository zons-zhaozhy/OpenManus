"""
Logging utility tests
"""

import logging
from pathlib import Path

import pytest

from app.utils.logging import LogFormatter, setup_logging


@pytest.fixture
def log_dir(tmp_path):
    """Create temporary log directory"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


def test_setup_logging(log_dir):
    """Test logging setup"""
    logger = setup_logging(log_dir=str(log_dir))
    assert logger is not None
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO


def test_log_file_creation(log_dir):
    """Test log file creation"""
    logger = setup_logging(log_dir=str(log_dir))
    logger.info("Test log message")

    log_files = list(log_dir.glob("*.log"))
    assert len(log_files) == 1
    assert log_files[0].read_text().strip().endswith("Test log message")


def test_log_formatter():
    """Test log formatter"""
    formatter = LogFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "Test message" in formatted
    assert "[INFO]" in formatted


def test_log_levels(log_dir):
    """Test different log levels"""
    logger = setup_logging(log_dir=str(log_dir))

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    log_content = next(log_dir.glob("*.log")).read_text()
    assert "Debug message" not in log_content  # Debug is not logged by default
    assert "Info message" in log_content
    assert "Warning message" in log_content
    assert "Error message" in log_content


def test_log_rotation(log_dir):
    """Test log file rotation"""
    logger = setup_logging(log_dir=str(log_dir), max_size="1KB", backup_count=2)

    # Generate enough logs to trigger rotation
    for i in range(1000):
        logger.info(f"Test log message {i}")

    log_files = list(log_dir.glob("*.log*"))
    assert 1 <= len(log_files) <= 3  # Main log + up to 2 backups


def test_custom_log_level(log_dir):
    """Test custom log level setup"""
    logger = setup_logging(log_dir=str(log_dir), level=logging.DEBUG)
    logger.debug("Debug message")

    log_content = next(log_dir.glob("*.log")).read_text()
    assert "Debug message" in log_content


def test_invalid_log_dir():
    """Test invalid log directory handling"""
    with pytest.raises(ValueError):
        setup_logging(log_dir="/nonexistent/path")


def test_log_format_with_exception(log_dir):
    """Test logging with exception information"""
    logger = setup_logging(log_dir=str(log_dir))

    try:
        raise ValueError("Test error")
    except ValueError:
        logger.exception("An error occurred")

    log_content = next(log_dir.glob("*.log")).read_text()
    assert "An error occurred" in log_content
    assert "ValueError: Test error" in log_content
    assert "Traceback" in log_content


def test_log_handler_cleanup(log_dir):
    """Test log handler cleanup"""
    logger = setup_logging(log_dir=str(log_dir))
    initial_handlers = len(logger.handlers)

    # Setup logging again with the same logger
    logger = setup_logging(log_dir=str(log_dir))
    assert len(logger.handlers) == initial_handlers  # Should not duplicate handlers
