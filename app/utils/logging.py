"""
通用日志系统
提供结构化日志、上下文追踪、多级日志等功能
"""

import json
import logging
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from pydantic import BaseModel


class LogConfig(BaseModel):
    """日志配置"""

    name: str
    level: str = "INFO"
    log_file: Optional[str] = None
    console: bool = True
    json_format: bool = False
    extra_fields: Dict[str, Any] = {}
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


class JsonFormatter(logging.Formatter):
    """JSON格式化器"""

    def __init__(self, extra_fields: Dict[str, Any] = None):
        super().__init__()
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **self.extra_fields,
        }

        if hasattr(record, "trace_id"):
            data["trace_id"] = record.trace_id

        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_fields"):
            data.update(record.extra_fields)

        return json.dumps(data, ensure_ascii=False)


class Logger:
    """日志记录器"""

    def __init__(self, config: LogConfig):
        """初始化日志记录器

        Args:
            config: 日志配置
        """
        self.config = config
        self.logger = logging.getLogger(config.name)
        self.logger.setLevel(config.level)
        self.logger.handlers = []  # 清除已有的处理器

        # 添加控制台处理器
        if config.console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(config.level)
            if config.json_format:
                formatter = JsonFormatter(config.extra_fields)
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 添加文件处理器
        if config.log_file:
            log_path = Path(config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=config.max_bytes,
                backupCount=config.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(config.level)
            if config.json_format:
                formatter = JsonFormatter(config.extra_fields)
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, extra: Dict[str, Any] = None):
        """记录调试日志"""
        self._log(logging.DEBUG, msg, extra)

    def info(self, msg: str, extra: Dict[str, Any] = None):
        """记录信息日志"""
        self._log(logging.INFO, msg, extra)

    def warning(self, msg: str, extra: Dict[str, Any] = None):
        """记录警告日志"""
        self._log(logging.WARNING, msg, extra)

    def error(self, msg: str, extra: Dict[str, Any] = None):
        """记录错误日志"""
        self._log(logging.ERROR, msg, extra)

    def critical(self, msg: str, extra: Dict[str, Any] = None):
        """记录严重错误日志"""
        self._log(logging.CRITICAL, msg, extra)

    def _log(self, level: int, msg: str, extra: Dict[str, Any] = None):
        """记录日志

        Args:
            level: 日志级别
            msg: 日志消息
            extra: 额外字段
        """
        if extra:
            self.logger.log(level, msg, extra={"extra_fields": extra})
        else:
            self.logger.log(level, msg)


def with_logging(
    logger: Logger, operation: str, log_args: bool = True, log_result: bool = True
):
    """日志装饰器

    Args:
        logger: 日志记录器
        operation: 操作名称
        log_args: 是否记录参数
        log_result: 是否记录返回值
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 记录开始日志
            extra = {}
            if log_args:
                # 过滤掉self参数
                func_args = args[1:] if args else []
                extra["args"] = str(func_args)
                extra["kwargs"] = str(kwargs)

            logger.info(f"开始{operation}", extra=extra)

            try:
                result = await func(*args, **kwargs)
                # 记录成功日志
                if log_result:
                    extra["result"] = str(result)
                logger.info(f"{operation}成功", extra=extra)
                return result
            except Exception as e:
                # 记录错误日志
                extra["error"] = str(e)
                logger.error(f"{operation}失败", extra=extra)
                raise

        return wrapper

    return decorator


# 默认日志记录器
default_logger = Logger(
    LogConfig(name="openmanus", level="INFO", console=True, json_format=True)
)
