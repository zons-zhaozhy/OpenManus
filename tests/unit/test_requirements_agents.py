"""
需求分析智能体的单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.assistants.requirements.agents.requirement_clarifier import (
    RequirementClarifierAgent,
    RequirementDimension,
)
from app.core.types import AgentResponse


@pytest.fixture
def mock_config():
    """模拟配置"""
    mock = MagicMock()
    mock.get_llm_config.return_value = {
        "api_base": "http://mock-api",
        "api_key": "mock-key",
        "model": "mock-model",
        "max_tokens": 2000,
        "temperature": 0.7,
    }
    return mock


@pytest.fixture
def mock_llm():
    """模拟LLM"""
    mock = AsyncMock()
    mock.ask = AsyncMock(
        return_value="分析结果：\n1. 功能需求...\n2. 性能要求...\n3. 业务目标..."
    )
    return mock


@pytest.fixture
def clarifier_agent(mock_llm, mock_config):
    """创建需求澄清智能体"""
    with patch("app.llm.LLM") as mock_llm_class, patch("app.llm.config", mock_config):
        mock_llm_class.return_value = mock_llm
        agent = RequirementClarifierAgent()
        return agent


@pytest.mark.asyncio
async def test_execute_basic_flow(clarifier_agent):
    """测试基本执行流程"""
    # 准备测试数据
    content = "我需要一个在线商城系统"

    # 执行测试
    result = await clarifier_agent.execute(content)

    # 验证结果
    assert isinstance(result, AgentResponse)
    assert (
        result.content == "分析结果：\n1. 功能需求...\n2. 性能要求...\n3. 业务目标..."
    )
    assert result.confidence >= 0.5
    assert result.metadata["dimension"] == RequirementDimension.FUNCTIONAL.value


@pytest.mark.asyncio
async def test_dimension_switching(clarifier_agent):
    """测试维度切换"""
    # 记录初始维度
    initial_dimension = clarifier_agent.current_dimension

    # 切换维度
    await clarifier_agent.switch_dimension()

    # 验证维度已切换
    assert clarifier_agent.current_dimension != initial_dimension
    assert clarifier_agent.current_dimension in RequirementDimension


@pytest.mark.asyncio
async def test_quality_score_tracking(clarifier_agent):
    """测试质量分数跟踪"""
    # 执行分析
    await clarifier_agent.execute("测试需求")

    # 验证质量分数
    score = clarifier_agent.get_quality_score()
    assert 0 <= score <= 1

    # 验证维度完成判断
    for dimension in RequirementDimension:
        is_complete = clarifier_agent.is_dimension_complete(dimension)
        assert isinstance(is_complete, bool)


@pytest.mark.asyncio
async def test_unclear_points_identification(clarifier_agent):
    """测试不明确点识别"""
    # 执行分析
    result = await clarifier_agent.execute("测试需求")

    # 验证不明确点
    assert "unclear_points" in result.metadata
    assert isinstance(result.metadata["unclear_points"], list)


@pytest.mark.asyncio
async def test_question_generation(clarifier_agent):
    """测试问题生成"""
    # 执行分析
    result = await clarifier_agent.execute("测试需求")

    # 验证问题
    assert isinstance(result.questions, list)
    for question in result.questions:
        assert isinstance(question, str)
        assert len(question) > 0


@pytest.mark.asyncio
async def test_confidence_calculation(clarifier_agent):
    """测试置信度计算"""
    # 执行分析
    result = await clarifier_agent.execute("测试需求")

    # 验证置信度
    assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_error_handling(clarifier_agent, mock_llm):
    """测试错误处理"""
    # 模拟错误
    mock_llm.ask.side_effect = Exception("测试错误")

    # 验证错误处理
    with pytest.raises(Exception) as exc_info:
        await clarifier_agent.execute("测试需求")

    assert "测试错误" in str(exc_info.value)
