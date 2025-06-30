"""
需求分析器测试
"""

from unittest.mock import AsyncMock, Mock

import pytest

from app.assistants.requirements.analyzer.services.requirement_analyzer import (
    ConflictResult,
    RequirementAnalysis,
    RequirementAnalyzer,
    ValidationResult,
)
from app.assistants.requirements.common.exceptions.requirement import (
    RequirementAnalysisError,
)
from app.assistants.requirements.storage.interfaces.storage import IRequirementStorage


@pytest.mark.asyncio
async def test_detect_conflicts():
    """测试需求冲突检测"""
    # 准备测试数据
    requirement = Mock()
    requirement.id = "REQ-001"
    requirement.description = "实现用户登录功能"
    requirement.priority = "high"
    requirement.status = "draft"
    requirement.dependencies = []

    existing_requirement = Mock()
    existing_requirement.id = "REQ-002"
    existing_requirement.description = "实现第三方登录功能"
    existing_requirement.priority = "medium"
    existing_requirement.status = "approved"
    existing_requirement.dependencies = []

    # 模拟LLM响应
    mock_llm = AsyncMock()
    mock_response = Mock()
    mock_response.tool_calls = [Mock()]
    mock_response.tool_calls[
        0
    ].function.arguments = """{
        "has_conflicts": true,
        "conflicts": [
            {
                "type": "functional_overlap",
                "description": "登录功能存在重叠",
                "severity": "medium",
                "affected_requirements": ["REQ-001", "REQ-002"]
            }
        ],
        "resolution_suggestions": [
            "建议合并两个登录需求，统一实现用户认证系统"
        ]
    }"""
    mock_llm.ask_tool = AsyncMock(return_value=mock_response)

    # 创建分析器实例
    storage = Mock(spec=IRequirementStorage)
    analyzer = RequirementAnalyzer(storage, mock_llm)

    # 执行测试
    result = await analyzer.detect_conflicts(requirement, [existing_requirement])

    # 验证结果
    assert isinstance(result, ConflictResult)
    assert result.has_conflicts is True
    assert len(result.conflicts) == 1
    assert result.conflicts[0].type == "functional_overlap"
    assert result.conflicts[0].description == "登录功能存在重叠"
    assert result.conflicts[0].severity == "medium"
    assert result.conflicts[0].affected_requirements == ["REQ-001", "REQ-002"]
    assert len(result.resolution_suggestions) == 1
    assert (
        result.resolution_suggestions[0] == "建议合并两个登录需求，统一实现用户认证系统"
    )


@pytest.mark.asyncio
async def test_detect_conflicts_no_conflicts():
    """测试无冲突情况"""
    # 准备测试数据
    requirement = Mock()
    requirement.id = "REQ-001"
    requirement.description = "实现用户头像上传功能"
    requirement.priority = "medium"
    requirement.status = "draft"
    requirement.dependencies = []

    existing_requirement = Mock()
    existing_requirement.id = "REQ-002"
    existing_requirement.description = "实现用户密码重置功能"
    existing_requirement.priority = "high"
    existing_requirement.status = "approved"
    existing_requirement.dependencies = []

    # 模拟LLM响应
    mock_llm = AsyncMock()
    mock_response = Mock()
    mock_response.tool_calls = [Mock()]
    mock_response.tool_calls[
        0
    ].function.arguments = """{
        "has_conflicts": false,
        "conflicts": [],
        "resolution_suggestions": []
    }"""
    mock_llm.ask_tool = AsyncMock(return_value=mock_response)

    # 创建分析器实例
    storage = Mock(spec=IRequirementStorage)
    analyzer = RequirementAnalyzer(storage, mock_llm)

    # 执行测试
    result = await analyzer.detect_conflicts(requirement, [existing_requirement])

    # 验证结果
    assert isinstance(result, ConflictResult)
    assert result.has_conflicts is False
    assert len(result.conflicts) == 0
    assert len(result.resolution_suggestions) == 0


@pytest.mark.asyncio
async def test_detect_conflicts_error():
    """测试错误处理"""
    # 准备测试数据
    requirement = Mock()
    requirement.id = "REQ-001"
    requirement.description = "测试需求"
    requirement.priority = "low"
    requirement.status = "draft"
    requirement.dependencies = []

    # 模拟LLM错误
    mock_llm = AsyncMock()
    mock_llm.ask_tool = AsyncMock(side_effect=Exception("LLM调用失败"))

    # 创建分析器实例
    storage = Mock(spec=IRequirementStorage)
    analyzer = RequirementAnalyzer(storage, mock_llm)

    # 验证异常抛出
    with pytest.raises(RequirementAnalysisError) as exc_info:
        await analyzer.detect_conflicts(requirement, [])

    assert "Failed to detect conflicts" in str(exc_info.value)
