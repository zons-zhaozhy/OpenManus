import sys
from datetime import datetime

from loguru import logger as _logger

from app.config import PROJECT_ROOT

_print_level = "INFO"


def define_log_level(print_level="INFO", logfile_level="DEBUG", name: str = None):
    """Adjust the log level to above level"""
    global _print_level
    _print_level = print_level

    # 使用固定的backend.log文件名
    log_name = "backend"

    _logger.remove()
    # 控制台输出保持原格式
    _logger.add(sys.stderr, level=print_level)
    # 文件输出使用固定文件名，并添加时间格式
    _logger.add(
        PROJECT_ROOT / f"logs/{log_name}.log",
        level=logfile_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="100 MB",  # 文件大小轮转
        retention="7 days",  # 保留7天的日志
    )
    return _logger


logger = define_log_level()


if __name__ == "__main__":
    logger.info("Starting application")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
