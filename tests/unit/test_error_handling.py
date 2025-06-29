"""
错误处理机制测试

测试新的统一错误处理机制
"""

import pytest
from fastapi import HTTPException

from app.api.requirements_modular.exceptions import (
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
from app.api.requirements_modular.utils.error_handler import (
    handle_error,
    wrap_error_handler,
)


# 测试基本异常类
def test_base_exception():
    error = RequirementAnalysisError("测试错误")
    assert error.message == "测试错误"
    assert error.details == {}

    error_with_details = RequirementAnalysisError("测试错误", {"key": "value"})
    assert error_with_details.message == "测试错误"
    assert error_with_details.details == {"key": "value"}


# 测试错误处理函数
def test_handle_error():
    # 测试基本错误
    error = RequirementAnalysisError("测试错误")
    result = handle_error(error)
    assert isinstance(result, HTTPException)
    assert result.status_code == 500
    assert result.detail["error"]["message"] == "测试错误"

    # 测试带详情的错误
    error_with_details = RequirementAnalysisError("测试错误", {"key": "value"})
    result = handle_error(error_with_details, include_details=True)
    assert result.detail["error"]["details"] == {"key": "value"}

    # 测试不同类型的错误
    invalid_session = InvalidSessionError("无效会话")
    result = handle_error(invalid_session)
    assert result.status_code == 404

    timeout = AnalysisTimeoutError("分析超时")
    result = handle_error(timeout)
    assert result.status_code == 504


# 测试装饰器
@pytest.mark.asyncio
async def test_wrap_error_handler():
    # 测试正常函数
    @wrap_error_handler
    async def normal_function():
        return {"status": "ok"}

    result = await normal_function()
    assert result == {"status": "ok"}

    # 测试抛出异常的函数
    @wrap_error_handler
    async def error_function():
        raise InvalidInputError("无效输入")

    with pytest.raises(HTTPException) as exc_info:
        await error_function()
    assert exc_info.value.status_code == 400


# 测试会话相关异常
def test_session_errors():
    # 测试无效会话
    error = InvalidSessionError("无效的会话ID")
    result = handle_error(error)
    assert result.status_code == 404

    # 测试会话过期
    error = SessionExpiredError("会话已过期")
    result = handle_error(error)
    assert result.status_code == 410


# 测试分析相关异常
def test_analysis_errors():
    # 测试分析错误
    error = AnalysisError("分析失败")
    result = handle_error(error)
    assert result.status_code == 500

    # 测试分析超时
    error = AnalysisTimeoutError("分析超时")
    result = handle_error(error)
    assert result.status_code == 504


# 测试工作流相关异常
def test_workflow_errors():
    error = WorkflowError("工作流执行失败")
    result = handle_error(error)
    assert result.status_code == 500


# 测试存储相关异常
def test_storage_errors():
    error = StorageError("存储操作失败")
    result = handle_error(error)
    assert result.status_code == 500


# 测试性能相关异常
def test_performance_errors():
    error = PerformanceError("性能问题")
    result = handle_error(error)
    assert result.status_code == 503


# 测试错误日志记录
def test_error_logging(caplog):
    error = RequirementAnalysisError("测试错误", {"key": "value"})
    handle_error(error, log_error=True)
    assert "测试错误" in caplog.text


# 测试异常继承关系
def test_exception_inheritance():
    # 测试会话异常继承
    assert issubclass(InvalidSessionError, SessionError)
    assert issubclass(SessionExpiredError, SessionError)
    assert issubclass(SessionError, RequirementAnalysisError)

    # 测试分析异常继承
    assert issubclass(AnalysisTimeoutError, AnalysisError)
    assert issubclass(AnalysisError, RequirementAnalysisError)


# 测试复杂场景
@pytest.mark.asyncio
async def test_complex_scenario():
    @wrap_error_handler
    async def complex_function(should_fail: bool = False):
        if should_fail:
            if should_fail == "timeout":
                raise AnalysisTimeoutError("操作超时")
            elif should_fail == "invalid_input":
                raise InvalidInputError("无效输入")
            else:
                raise RequirementAnalysisError("未知错误")
        return {"status": "ok"}

    # 测试成功场景
    result = await complex_function(should_fail=False)
    assert result == {"status": "ok"}

    # 测试超时场景
    with pytest.raises(HTTPException) as exc_info:
        await complex_function(should_fail="timeout")
    assert exc_info.value.status_code == 504

    # 测试无效输入场景
    with pytest.raises(HTTPException) as exc_info:
        await complex_function(should_fail="invalid_input")
    assert exc_info.value.status_code == 400

    # 测试未知错误场景
    with pytest.raises(HTTPException) as exc_info:
        await complex_function(should_fail=True)
    assert exc_info.value.status_code == 500
