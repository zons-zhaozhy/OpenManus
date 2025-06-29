"""
测试RequirementsFlow的功能
"""

from unittest.mock import Mock, patch

import pytest

from app.assistants.requirements.flow import RequirementsFlow
from app.flow.mixins import ErrorSeverity


@pytest.fixture
def requirements_flow():
    """创建RequirementsFlow实例"""
    return RequirementsFlow(project_id="test-project-001")


@pytest.mark.asyncio
async def test_project_management_mixin(requirements_flow):
    """测试项目管理Mixin的功能"""
    # 验证项目上下文加载
    assert requirements_flow.project_id == "test-project-001"
    assert requirements_flow.project_context is not None

    # 验证项目指引生成
    guidance = requirements_flow._build_project_guidance_prompt()
    assert "项目目标" in guidance
    assert "项目背景" in guidance
    assert "成功标准" in guidance
    assert "约束条件" in guidance


@pytest.mark.asyncio
async def test_error_handling_mixin(requirements_flow):
    """测试错误处理Mixin的功能"""
    # 测试错误记录
    test_error = ValueError("测试错误")
    requirements_flow.record_error(
        error=test_error, stage="测试阶段", severity=ErrorSeverity.MEDIUM
    )

    # 验证错误历史
    assert len(requirements_flow.error_history) == 1
    error_record = requirements_flow.error_history[0]
    assert error_record["error_type"] == "ValueError"
    assert error_record["stage"] == "测试阶段"
    assert error_record["severity"] == ErrorSeverity.MEDIUM
    assert "stack_trace" in error_record

    # 测试错误摘要
    summary = requirements_flow.get_error_summary()
    assert summary["status"] == "error"
    assert summary["error_count"] == 1
    assert summary["retry_attempts"] == 0
    assert summary["can_retry"] is True

    # 测试重试逻辑
    assert requirements_flow.can_retry(test_error) is True
    requirements_flow.current_retry = 3
    assert requirements_flow.can_retry(test_error) is False

    # 测试不可重试错误
    not_implemented_error = NotImplementedError("不可重试错误")
    assert requirements_flow.can_retry(not_implemented_error) is False

    # 测试错误状态重置
    requirements_flow.reset_error_state()
    assert len(requirements_flow.error_history) == 0
    assert requirements_flow.current_retry == 0


@pytest.mark.asyncio
async def test_clarify_requirements_enhanced(requirements_flow):
    """测试增强的需求澄清功能"""
    with patch.object(requirements_flow, "get_agent") as mock_get_agent:
        # 模拟智能体
        mock_agent = Mock()
        mock_agent.run.return_value = "测试澄清结果"
        mock_get_agent.return_value = mock_agent

        # 执行澄清
        result = await requirements_flow._clarify_requirements_enhanced("测试需求")

        # 验证结果
        assert result == "测试澄清结果"
        assert requirements_flow.clarification_complete is True
        assert "clarification" in requirements_flow.current_context


@pytest.mark.asyncio
async def test_analyze_business_enhanced(requirements_flow):
    """测试增强的业务分析功能"""
    with patch.object(requirements_flow, "get_agent") as mock_get_agent:
        # 模拟智能体
        mock_agent = Mock()
        mock_agent.run.return_value = "测试分析结果"
        mock_get_agent.return_value = mock_agent

        # 执行分析
        result = await requirements_flow._analyze_business_enhanced("测试澄清结果")

        # 验证结果
        assert result == "测试分析结果"
        assert requirements_flow.analysis_complete is True
        assert "analysis" in requirements_flow.current_context


@pytest.mark.asyncio
async def test_write_documentation_enhanced(requirements_flow):
    """测试增强的文档编写功能"""
    with patch.object(requirements_flow, "get_agent") as mock_get_agent:
        # 模拟智能体
        mock_agent = Mock()
        mock_agent.run.return_value = "测试文档结果"
        mock_get_agent.return_value = mock_agent

        # 执行文档编写
        result = await requirements_flow._write_documentation_enhanced("测试分析结果")

        # 验证结果
        assert result == "测试文档结果"
        assert "documentation" in requirements_flow.current_context


@pytest.mark.asyncio
async def test_quality_review_enhanced(requirements_flow):
    """测试增强的质量评审功能"""
    with patch.object(requirements_flow, "get_agent") as mock_get_agent:
        # 模拟智能体
        mock_agent = Mock()
        mock_agent.run.return_value = "测试评审结果"
        mock_get_agent.return_value = mock_agent

        # 执行质量评审
        result = await requirements_flow._quality_review_enhanced("测试文档结果")

        # 验证结果
        assert result == "测试评审结果"
        assert "review" in requirements_flow.current_context


@pytest.mark.asyncio
async def test_error_handling_in_flow(requirements_flow):
    """测试流程中的错误处理"""
    with patch.object(requirements_flow, "get_agent") as mock_get_agent:
        # 模拟会抛出错误的智能体
        mock_agent = Mock()
        mock_agent.run.side_effect = ValueError("测试错误")
        mock_get_agent.return_value = mock_agent

        # 测试澄清阶段的错误处理
        with pytest.raises(ValueError):
            await requirements_flow._clarify_requirements_enhanced("测试需求")

        # 验证错误记录
        assert len(requirements_flow.error_history) == 1
        error_record = requirements_flow.error_history[0]
        assert error_record["error_type"] == "ValueError"
        assert error_record["stage"] == "需求澄清"
        assert error_record["severity"] == ErrorSeverity.HIGH

        # 验证重试计数
        assert requirements_flow.current_retry == 1

        # 验证状态管理器
        assert requirements_flow.state_manager.current_state == FlowState.FAILED.value


@pytest.mark.asyncio
async def test_async_error_handling(requirements_flow):
    """测试异步错误处理"""

    # 模拟异步错误
    async def async_error():
        raise ValueError("异步错误")

    # 测试异步错误处理
    with pytest.raises(ValueError):
        await requirements_flow.handle_error_with_retry(
            ValueError("异步错误"),
            "异步测试",
            ErrorSeverity.MEDIUM,
            {"async": True},
        )

    # 验证错误记录
    assert len(requirements_flow.error_history) == 1
    error_record = requirements_flow.error_history[0]
    assert error_record["error_type"] == "ValueError"
    assert error_record["stage"] == "异步测试"
    assert error_record["context"]["async"] is True


@pytest.mark.asyncio
async def test_error_severity_handling(requirements_flow):
    """测试错误严重程度处理"""
    # 测试不同严重程度的错误
    severities = [
        ErrorSeverity.LOW,
        ErrorSeverity.MEDIUM,
        ErrorSeverity.HIGH,
        ErrorSeverity.CRITICAL,
    ]

    for severity in severities:
        requirements_flow.record_error(
            ValueError(f"{severity}错误"),
            f"{severity}测试",
            severity,
        )

    # 验证错误统计
    summary = requirements_flow.get_error_summary()
    assert len(summary["error_types"]) == 1  # 都是ValueError
    assert sum(summary["severity_counts"].values()) == len(severities)

    # 验证严重错误的状态转换
    assert requirements_flow.state_manager.current_state == FlowState.FAILED.value


@pytest.mark.asyncio
async def test_parallel_error_handling(requirements_flow):
    """测试并行执行中的错误处理"""

    # 模拟并行任务错误
    async def failing_task():
        raise ValueError("并行任务错误")

    # 执行并行任务
    tasks = [failing_task(), failing_task()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 验证所有错误都被捕获
    assert all(isinstance(r, ValueError) for r in results)


@pytest.mark.asyncio
async def test_error_context_tracking(requirements_flow):
    """测试错误上下文跟踪"""
    # 测试带上下文的错误记录
    context = {
        "user_input": "测试输入",
        "stage": "测试阶段",
        "agent": "测试智能体",
    }

    requirements_flow.record_error(
        ValueError("上下文错误"),
        "上下文测试",
        ErrorSeverity.MEDIUM,
        context,
    )

    # 验证错误上下文
    error_record = requirements_flow.error_history[0]
    assert error_record["context"] == context
    assert "timestamp" in error_record
    assert "stack_trace" in error_record


@pytest.mark.asyncio
async def test_error_recovery(requirements_flow):
    """测试错误恢复"""
    # 记录一些错误
    for i in range(3):
        requirements_flow.record_error(
            ValueError(f"错误{i}"),
            f"阶段{i}",
            ErrorSeverity.MEDIUM,
        )

    # 验证错误状态
    assert len(requirements_flow.error_history) == 3
    assert requirements_flow.current_retry == 0

    # 重置错误状态
    requirements_flow.reset_error_state()

    # 验证恢复
    assert len(requirements_flow.error_history) == 0
    assert requirements_flow.current_retry == 0
    assert requirements_flow.state_manager.error_count == 0
