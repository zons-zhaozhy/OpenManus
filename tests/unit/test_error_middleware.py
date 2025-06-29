"""
错误处理中间件测试

测试错误处理中间件的功能
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.requirements_modular import create_app
from app.api.requirements_modular.exceptions import (
    AnalysisError,
    InvalidInputError,
    RequirementAnalysisError,
)
from app.api.requirements_modular.middleware.error_middleware import (
    ErrorHandlingMiddleware,
    error_handler,
)


@pytest.fixture
def test_app():
    """创建测试应用"""
    app = create_app()
    return app


@pytest.fixture
def test_client(test_app):
    """创建测试客户端"""
    return TestClient(test_app)


def test_error_middleware_handles_requirement_analysis_error(test_client):
    """测试中间件处理业务异常"""
    # 创建一个测试路由
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/test/error")
    async def test_error():
        raise RequirementAnalysisError("测试错误")

    client = TestClient(app)
    response = client.get("/test/error")

    assert response.status_code == 500
    assert response.json()["error"]["type"] == "RequirementAnalysisError"
    assert response.json()["error"]["message"] == "测试错误"


def test_error_middleware_handles_invalid_input_error(test_client):
    """测试中间件处理输入错误"""
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.post("/test/input")
    async def test_input():
        raise InvalidInputError("无效输入")

    client = TestClient(app)
    response = client.post("/test/input")

    assert response.status_code == 400
    assert response.json()["error"]["type"] == "InvalidInputError"
    assert response.json()["error"]["message"] == "无效输入"


def test_error_middleware_handles_unknown_error(test_client):
    """测试中间件处理未知错误"""
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/test/unknown")
    async def test_unknown():
        raise ValueError("未知错误")

    client = TestClient(app)
    response = client.get("/test/unknown")

    assert response.status_code == 500
    assert response.json()["error"]["type"] == "ValueError"
    assert response.json()["error"]["message"] == "未知错误"


def test_error_middleware_logs_request_info(test_client, caplog):
    """测试中间件记录请求信息"""
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/test/log")
    async def test_log():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get(
        "/test/log",
        headers={"X-Request-ID": "test-123", "User-Agent": "test-agent"},
    )

    assert response.status_code == 200
    assert "收到请求: GET /test/log" in caplog.text
    assert "请求完成: GET /test/log - 200" in caplog.text


def test_error_middleware_handles_analysis_error_with_details(test_client):
    """测试中间件处理带详情的分析错误"""
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/test/analysis")
    async def test_analysis():
        raise AnalysisError(
            "分析失败",
            details={
                "stage": "需求分析",
                "reason": "输入不完整",
                "missing_fields": ["description", "priority"],
            },
        )

    client = TestClient(app)
    response = client.get("/test/analysis")

    assert response.status_code == 500
    assert response.json()["error"]["type"] == "AnalysisError"
    assert response.json()["error"]["message"] == "分析失败"
    assert response.json()["error"]["details"]["stage"] == "需求分析"
    assert response.json()["error"]["details"]["reason"] == "输入不完整"
    assert "description" in response.json()["error"]["details"]["missing_fields"]


def test_error_handler_decorator():
    """测试错误处理装饰器"""

    @error_handler
    def test_function(should_fail: bool = False):
        if should_fail:
            raise InvalidInputError("测试错误")
        return {"status": "ok"}

    # 测试正常情况
    result = test_function(should_fail=False)
    assert result == {"status": "ok"}

    # 测试错误情况
    result = test_function(should_fail=True)
    assert result.status_code == 400
    assert result.body.decode().find("InvalidInputError") > 0


def test_error_middleware_preserves_successful_response(test_client):
    """测试中间件保持成功响应不变"""
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/test/success")
    async def test_success():
        return {"status": "success", "data": {"key": "value"}}

    client = TestClient(app)
    response = client.get("/test/success")

    assert response.status_code == 200
    assert response.json() == {"status": "success", "data": {"key": "value"}}
