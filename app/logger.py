"""
日志配置
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import Config

settings = Config()

# 创建日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 配置日志格式
formatter = logging.Formatter(settings.LOG_FORMAT)

# 创建文件处理器
file_handler = RotatingFileHandler(
    log_dir / "app.log", maxBytes=10_000_000, backupCount=5  # 10MB
)
file_handler.setFormatter(formatter)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# 配置根日志器
logger = logging.getLogger("app")
logger.setLevel(settings.LOG_LEVEL)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器

    Args:
        name: 日志器名称，通常是模块名

    Returns:
        logging.Logger: 配置好的日志器
    """
    module_logger = logging.getLogger(f"app.{name}")
    module_logger.setLevel(settings.LOG_LEVEL)

    # 避免重复添加处理器
    if not module_logger.handlers:
        module_logger.addHandler(file_handler)
        module_logger.addHandler(console_handler)

    return module_logger


def log_exception(logger, message: str, exc: Exception, level: int = logging.ERROR):
    """
    记录异常日志

    Args:
        logger: 日志器实例
        message: 日志消息
        exc: 异常对象
        level: 日志级别
    """
    import traceback

    logger.log(level, f"{message}: {exc}")
    logger.log(level, traceback.format_exc())
