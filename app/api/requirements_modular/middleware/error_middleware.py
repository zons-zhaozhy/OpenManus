"""
错误处理中间件

为所有API提供统一的错误处理
"""

from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.logger import logger

from ..exceptions import RequirementAnalysisError
from ..utils.error_handler import handle_error


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """处理请求"""
        try:
            # 记录请求信息
            logger.info(
                f"收到请求: {request.method} {request.url.path}",
                extra={
                    "request_id": request.headers.get("X-Request-ID"),
                    "user_agent": request.headers.get("User-Agent"),
                },
            )

            # 执行请求
            response = await call_next(request)

            # 记录响应信息
            logger.info(
                f"请求完成: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request.headers.get("X-Request-ID"),
                    "status_code": response.status_code,
                },
            )

            return response

        except RequirementAnalysisError as e:
            # 处理业务异常
            error_response = handle_error(e)
            return JSONResponse(
                status_code=error_response.status_code,
                content=error_response.detail,
            )

        except Exception as e:
            # 处理未知异常
            logger.error(
                f"未知错误: {str(e)}",
                exc_info=True,
                extra={
                    "request_id": request.headers.get("X-Request-ID"),
                    "path": request.url.path,
                },
            )
            error_response = handle_error(e)
            return JSONResponse(
                status_code=error_response.status_code,
                content=error_response.detail,
            )


def setup_error_handling(app: FastAPI) -> None:
    """设置错误处理中间件"""
    app.add_middleware(ErrorHandlingMiddleware)


def error_handler(func: Callable) -> Callable:
    """错误处理装饰器 - 用于非异步函数"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_response = handle_error(e)
            return JSONResponse(
                status_code=error_response.status_code,
                content=error_response.detail,
            )

    return wrapper
