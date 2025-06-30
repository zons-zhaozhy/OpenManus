"""
需求分析器测试
"""

from unittest.mock import AsyncMock, Mock

import pytest

from ..models.base import Requirement
from ..services.requirement_analyzer import (
    RequirementAnalysis,
    RequirementAnalyzer,
    Suggestion,
    ValidationResult,
)
from ..utils.exceptions import RequirementAnalysisError


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.fixture
def mock_storage():
    return AsyncMock()


@pytest.fixture
def analyzer(mock_storage, mock_llm):
    return RequirementAnalyzer(requirement_storage=mock_storage, llm=mock_llm)


@pytest.mark.asyncio
async def test_analyze_requirement_success(analyzer, mock_llm):
    # 准备测试数据
    test_text = "实现用户登录功能，包括账号密码验证和记住登录状态"
    expected_analysis = {
        "requirement_points": ["用户登录功能", "账号密码验证", "记住登录状态"],
        "requirement_type": "functional",
        "priority": "high",
        "dependencies": ["用户系统", "认证服务"],
        "acceptance_criteria": [
            "用户能够使用正确的账号密码登录",
            "登录状态能够被正确保存",
        ],
        "risk_points": ["密码安全性", "session管理"],
    }

    # 模拟LLM响应
    mock_llm.ask_tool.return_value = AsyncMock(
        tool_calls=[Mock(function=Mock(arguments=str(expected_analysis)))]
    )

    # 执行测试
    result = await analyzer.analyze_requirement(test_text)

    # 验证结果
    assert isinstance(result, RequirementAnalysis)
    assert result.requirement_points == expected_analysis["requirement_points"]
    assert result.requirement_type == expected_analysis["requirement_type"]
    assert result.priority == expected_analysis["priority"]
    assert result.dependencies == expected_analysis["dependencies"]
    assert result.acceptance_criteria == expected_analysis["acceptance_criteria"]
    assert result.risk_points == expected_analysis["risk_points"]


@pytest.mark.asyncio
async def test_analyze_requirement_failure(analyzer, mock_llm):
    # 模拟LLM错误
    mock_llm.ask_tool.return_value = None

    # 验证异常抛出
    with pytest.raises(RequirementAnalysisError):
        await analyzer.analyze_requirement("测试需求")


@pytest.mark.asyncio
async def test_validate_requirement_success(analyzer, mock_llm):
    # 准备测试数据
    test_requirement = Requirement(
        id="REQ-001",
        project_id="PROJ-001",
        description="实现用户登录功能",
        priority="high",
        status="new",
        dependencies=[],
    )
    expected_validation = {
        "is_valid": True,
        "issues": [],
        "suggestions": ["可以添加更详细的验收标准"],
    }

    # 模拟LLM响应
    mock_llm.ask_tool.return_value = AsyncMock(
        tool_calls=[Mock(function=Mock(arguments=str(expected_validation)))]
    )

    # 执行测试
    result = await analyzer.validate_requirement(test_requirement)

    # 验证结果
    assert isinstance(result, ValidationResult)
    assert result.is_valid == expected_validation["is_valid"]
    assert result.issues == expected_validation["issues"]
    assert result.suggestions == expected_validation["suggestions"]


@pytest.mark.asyncio
async def test_suggest_improvements_success(analyzer, mock_llm):
    # 准备测试数据
    test_requirement = Requirement(
        id="REQ-001",
        project_id="PROJ-001",
        description="实现用户登录功能",
        priority="high",
        status="new",
        dependencies=[],
    )
    expected_suggestions = {
        "suggestions": [
            {
                "aspect": "描述完整性",
                "current_state": "描述过于简单",
                "suggested_change": "添加具体的功能点和约束条件",
                "reason": "帮助开发团队更好理解需求",
                "example": "实现用户登录功能，包括邮箱/手机号登录，密码强度验证，以及登录状态保持",
            }
        ]
    }

    # 模拟LLM响应
    mock_llm.ask_tool.return_value = AsyncMock(
        tool_calls=[Mock(function=Mock(arguments=str(expected_suggestions)))]
    )

    # 执行测试
    result = await analyzer.suggest_improvements(test_requirement)

    # 验证结果
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Suggestion)
    assert result[0].aspect == expected_suggestions["suggestions"][0]["aspect"]
    assert (
        result[0].current_state
        == expected_suggestions["suggestions"][0]["current_state"]
    )
    assert (
        result[0].suggested_change
        == expected_suggestions["suggestions"][0]["suggested_change"]
    )
    assert result[0].reason == expected_suggestions["suggestions"][0]["reason"]
    assert result[0].example == expected_suggestions["suggestions"][0]["example"]
