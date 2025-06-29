"""
错误处理工具模块

提供统一的异常处理函数
"""

from typing import Any, Dict, Optional, Type, Union

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.logger import logger

from ..exceptions import (
    AnalysisError,
    AnalysisTimeoutError,
    ClarificationError,
    InvalidInputError,
    InvalidSessionError,
    PerformanceError,
    RequirementAnalysisError,
    SessionError,
    SessionExpiredError,
    StorageError,
    WorkflowError,
)

# 异常到HTTP状态码的映射
ERROR_STATUS_CODES = {
    InvalidSessionError: 404,  # Not Found
    SessionExpiredError: 410,  # Gone
    InvalidInputError: 400,  # Bad Request
    AnalysisTimeoutError: 504,  # Gateway Timeout
    AnalysisError: 500,  # Internal Server Error
    ClarificationError: 500,
    WorkflowError: 500,
    StorageError: 500,
    PerformanceError: 503,  # Service Unavailable
    RequirementAnalysisError: 500,
    Exception: 500,  # 默认状态码
}


def handle_error(
    error: Exception,
    log_error: bool = True,
    include_details: bool = True,
) -> Union[Dict[str, Any], HTTPException]:
    """
    统一处理异常，返回标准化的错误响应

    Args:
        error: 异常对象
        log_error: 是否记录错误日志
        include_details: 是否包含详细错误信息

    Returns:
        Dict 或 HTTPException: 标准化的错误响应
    """
    # 获取错误类型
    error_type = type(error)

    # 获取状态码
    status_code = ERROR_STATUS_CODES.get(error_type, 500)

    # 构建错误消息
    if isinstance(error, RequirementAnalysisError):
        error_message = error.message
        error_details = error.details if include_details else {}
    else:
        error_message = str(error)
        error_details = {}

    # 记录错误日志
    if log_error:
        logger.error(
            f"错误类型: {error_type.__name__}, "
            f"消息: {error_message}, "
            f"详情: {error_details}",
            exc_info=True,
        )

    # 构建错误响应
    error_response = {
        "error": {
            "type": error_type.__name__,
            "message": error_message,
            "status_code": status_code,
        }
    }

    # 添加详细信息（如果需要）
    if include_details and error_details:
        error_response["error"]["details"] = error_details

    return HTTPException(
        status_code=status_code,
        detail=error_response,
    )


def wrap_error_handler(func: callable) -> callable:
    """
    装饰器：为函数添加统一的错误处理

    Args:
        func: 需要添加错误处理的函数

    Returns:
        callable: 包装后的函数
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            raise handle_error(e)

    return wrapper
