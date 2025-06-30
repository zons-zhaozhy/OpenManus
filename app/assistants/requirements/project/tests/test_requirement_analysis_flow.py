"""
需求分析流程测试
"""

from unittest.mock import AsyncMock, Mock

import pytest

from ..models.base import Project, Requirement
from ..services.memory_event_publisher import MemoryEventPublisher
from ..services.memory_storage import MemoryProjectStorage, MemoryRequirementStorage
from ..services.project_manager import ProjectManager
from ..services.requirement_analyzer import RequirementAnalyzer
from ..utils.validators import ProjectValidator, RequirementValidator


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.fixture
def project_storage():
    return MemoryProjectStorage()


@pytest.fixture
def requirement_storage():
    return MemoryRequirementStorage()


@pytest.fixture
def event_publisher():
    return MemoryEventPublisher()


@pytest.fixture
def requirement_analyzer(mock_llm, requirement_storage):
    return RequirementAnalyzer(requirement_storage=requirement_storage, llm=mock_llm)


@pytest.fixture
def project_manager(
    project_storage, requirement_storage, event_publisher, requirement_analyzer
):
    return ProjectManager(
        project_storage=project_storage,
        requirement_storage=requirement_storage,
        event_publisher=event_publisher,
        requirement_analyzer=requirement_analyzer,
        project_validator=ProjectValidator(),
        requirement_validator=RequirementValidator(),
    )


@pytest.mark.asyncio
async def test_requirement_analysis_flow(project_manager, mock_llm):
    # 1. 创建测试项目
    project = Project(
        id="TEST-PROJ-001", name="测试项目", description="用于测试需求分析流程"
    )
    created_project = await project_manager.create_project(project)
    assert created_project.id == project.id

    # 2. 准备测试数据
    requirement_text = """
    实现用户注册功能：
    1. 用户可以使用邮箱或手机号注册
    2. 密码必须符合安全要求（至少8位，包含大小写字母和数字）
    3. 需要邮箱或手机号验证
    4. 注册成功后自动登录
    """

    # 模拟需求分析响应
    analysis_response = {
        "requirement_points": [
            "支持邮箱和手机号注册",
            "密码安全要求验证",
            "邮箱/手机号验证",
            "注册后自动登录",
        ],
        "requirement_type": "functional",
        "priority": "high",
        "dependencies": ["用户系统", "认证服务", "通知服务"],
        "acceptance_criteria": [
            "用户可以使用邮箱成功注册",
            "用户可以使用手机号成功注册",
            "密码不符合要求时显示错误提示",
            "注册成功后用户处于登录状态",
        ],
        "risk_points": [
            "邮箱/手机号验证码发送失败",
            "并发注册导致的数据一致性问题",
            "用户信息安全存储",
        ],
    }
    mock_llm.ask_tool.return_value = AsyncMock(
        tool_calls=[Mock(function=Mock(arguments=str(analysis_response)))]
    )

    # 3. 分析需求文本
    analysis = await project_manager.analyze_requirement_text(requirement_text)
    assert analysis.requirement_type == "functional"
    assert analysis.priority == "high"
    assert len(analysis.requirement_points) == 4
    assert len(analysis.acceptance_criteria) == 4
    assert len(analysis.risk_points) == 3

    # 4. 从分析结果创建需求
    requirement = await project_manager.create_requirement_from_analysis(
        project_id=created_project.id, analysis=analysis
    )
    assert requirement.project_id == created_project.id
    assert requirement.type == analysis.requirement_type
    assert requirement.priority == analysis.priority
    assert len(requirement.acceptance_criteria) == len(analysis.acceptance_criteria)

    # 模拟需求验证响应
    validation_response = {
        "is_valid": True,
        "issues": [],
        "suggestions": ["可以添加性能相关的验收标准"],
    }
    mock_llm.ask_tool.return_value = AsyncMock(
        tool_calls=[Mock(function=Mock(arguments=str(validation_response)))]
    )

    # 5. 验证需求质量
    validation = await project_manager.validate_requirement_quality(requirement.id)
    assert validation.is_valid
    assert len(validation.suggestions) == 1

    # 模拟改进建议响应
    improvement_response = {
        "suggestions": [
            {
                "aspect": "性能要求",
                "current_state": "未指定性能要求",
                "suggested_change": "添加注册流程的响应时间要求",
                "reason": "确保良好的用户体验",
                "example": "注册流程的响应时间不超过2秒",
            }
        ]
    }
    mock_llm.ask_tool.return_value = AsyncMock(
        tool_calls=[Mock(function=Mock(arguments=str(improvement_response)))]
    )

    # 6. 获取改进建议
    improvements = await project_manager.get_requirement_improvements(requirement.id)
    assert len(improvements) == 1
    assert improvements[0].aspect == "性能要求"
    assert improvements[0].example is not None
