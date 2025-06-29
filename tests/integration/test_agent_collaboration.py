"""
测试智能体协作功能
"""

import asyncio
from datetime import datetime

import pytest

from app.assistants.requirements.collaboration_manager import CollaborationManager
from app.assistants.requirements.flow import RequirementsFlow
from app.core.types import AgentState, Message
from app.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
async def requirements_flow():
    """创建需求分析流程实例"""
    flow = RequirementsFlow()
    yield flow
    # 清理资源
    for agent in flow.agents.values():
        await flow.collaboration_manager.clear_agent_data(agent.id)


@pytest.mark.asyncio
async def test_agent_registration():
    """测试智能体注册"""
    flow = RequirementsFlow()

    # 验证所有智能体都已注册
    states = flow.collaboration_manager.get_all_states()
    assert len(states) == 4  # 应该有4个智能体

    # 验证每个智能体的初始状态
    for agent_id, state in states.items():
        assert state.state == AgentState.IDLE
        assert state.progress == 0.0
        assert state.current_task is None


@pytest.mark.asyncio
async def test_message_passing():
    """测试智能体间消息传递"""
    flow = RequirementsFlow()

    # 获取智能体
    clarifier = flow.get_agent("clarifier")
    analyst = flow.get_agent("analyst")

    # 发送消息
    test_message = Message.system_message("测试消息")
    await flow.collaboration_manager.send_message(
        clarifier.id, analyst.id, test_message
    )

    # 接收消息
    messages = await flow.collaboration_manager.get_messages(analyst.id)
    assert len(messages) == 1
    assert messages[0].content == "测试消息"


@pytest.mark.asyncio
async def test_state_updates():
    """测试状态更新"""
    flow = RequirementsFlow()
    clarifier = flow.get_agent("clarifier")

    # 更新状态
    await flow.collaboration_manager.update_state(
        clarifier.id, AgentState.RUNNING, task="测试任务", progress=0.5
    )

    # 验证状态
    state = flow.collaboration_manager.get_state(clarifier.id)
    assert state.state == AgentState.RUNNING
    assert state.current_task == "测试任务"
    assert state.progress == 0.5


@pytest.mark.asyncio
async def test_data_sharing():
    """测试数据共享"""
    flow = RequirementsFlow()
    clarifier = flow.get_agent("clarifier")

    # 共享数据
    test_data = {"key": "value"}
    await flow.collaboration_manager.share_data(clarifier.id, "test_data", test_data)

    # 验证共享数据
    shared_data = flow.collaboration_manager.get_shared_data("test_data")
    assert shared_data == test_data


@pytest.mark.asyncio
async def test_parallel_execution():
    """测试并行执行"""
    flow = RequirementsFlow(enable_parallel=True)

    # 模拟用户输入
    user_input = """
    我需要一个在线商城系统，主要功能包括：
    1. 用户注册登录
    2. 商品浏览和搜索
    3. 购物车
    4. 订单管理
    5. 支付功能
    """

    # 执行需求分析
    result = await flow.execute(user_input)

    # 验证所有智能体状态
    states = flow.collaboration_manager.get_all_states()
    for state in states.values():
        assert state.state == AgentState.COMPLETED
        assert state.progress == 1.0


@pytest.mark.asyncio
async def test_sequential_execution():
    """测试顺序执行"""
    flow = RequirementsFlow(enable_parallel=False)

    # 模拟用户输入
    user_input = """
    我需要一个任务管理系统，主要功能包括：
    1. 任务创建和分配
    2. 进度跟踪
    3. 团队协作
    4. 报表统计
    """

    # 执行需求分析
    result = await flow.execute(user_input)

    # 验证所有智能体状态
    states = flow.collaboration_manager.get_all_states()
    for state in states.values():
        assert state.state == AgentState.COMPLETED
        assert state.progress == 1.0


@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    flow = RequirementsFlow()
    clarifier = flow.get_agent("clarifier")

    # 模拟错误
    with pytest.raises(ValueError):
        await flow.collaboration_manager.update_state(
            "invalid_agent_id", AgentState.RUNNING
        )

    # 验证错误不影响其他智能体
    state = flow.collaboration_manager.get_state(clarifier.id)
    assert state.state == AgentState.IDLE


@pytest.mark.asyncio
async def test_state_waiting():
    """测试状态等待"""
    flow = RequirementsFlow()
    clarifier = flow.get_agent("clarifier")

    # 启动异步任务更新状态
    async def update_state_after_delay():
        await asyncio.sleep(1)
        await flow.collaboration_manager.update_state(clarifier.id, AgentState.RUNNING)

    # 等待状态变化
    asyncio.create_task(update_state_after_delay())
    result = await flow.collaboration_manager.wait_for_state(
        clarifier.id, AgentState.RUNNING, timeout=2.0
    )

    assert result is True


@pytest.mark.asyncio
async def test_clarification_process():
    """测试完整的需求澄清过程"""
    flow = RequirementsFlow()
    clarifier = flow.get_agent("clarifier")

    # 模拟用户输入
    requirement = "我需要一个简单的博客系统"

    # 执行澄清
    result = await clarifier.clarify(requirement)

    # 验证状态变化
    state = flow.collaboration_manager.get_state(clarifier.id)
    assert state.state == AgentState.COMPLETED
    assert state.progress == 1.0

    # 验证共享数据
    analysis = flow.collaboration_manager.get_shared_data("requirement_analysis")
    assert analysis is not None

    points = flow.collaboration_manager.get_shared_data("clarification_points")
    assert points is not None

    clarified = flow.collaboration_manager.get_shared_data("clarified_requirement")
    assert clarified is not None


@pytest.mark.asyncio
async def test_business_analysis_process():
    """测试业务分析流程"""
    flow = RequirementsFlow()
    analyst = flow.get_agent("analyst")

    # 模拟需求输入
    requirement = """
    需要开发一个企业级项目管理系统，主要功能包括：
    1. 项目创建和配置
    2. 任务分配和跟踪
    3. 资源管理
    4. 进度报告
    5. 风险管理
    6. 团队协作
    """

    # 执行业务分析
    result = await analyst.analyze(requirement)

    # 验证状态变化
    state = flow.collaboration_manager.get_state(analyst.id)
    assert state.state == AgentState.COMPLETED
    assert state.progress == 1.0

    # 验证共享数据
    process_analysis = flow.collaboration_manager.get_shared_data("process_analysis")
    assert process_analysis is not None

    business_rules = flow.collaboration_manager.get_shared_data("business_rules")
    assert business_rules is not None
    assert isinstance(business_rules, list)
    assert len(business_rules) > 0

    value_assessment = flow.collaboration_manager.get_shared_data("value_assessment")
    assert value_assessment is not None

    risk_assessment = flow.collaboration_manager.get_shared_data("risk_assessment")
    assert risk_assessment is not None


@pytest.mark.asyncio
async def test_business_analysis_error_handling():
    """测试业务分析错误处理"""
    flow = RequirementsFlow()
    analyst = flow.get_agent("analyst")

    # 模拟错误情况
    with pytest.raises(ValueError):
        await analyst.analyze("")

    # 验证错误状态
    state = flow.collaboration_manager.get_state(analyst.id)
    assert state.state == AgentState.ERROR

    # 验证错误不影响其他智能体
    clarifier = flow.get_agent("clarifier")
    clarifier_state = flow.collaboration_manager.get_state(clarifier.id)
    assert clarifier_state.state == AgentState.IDLE


@pytest.mark.asyncio
async def test_business_analysis_collaboration():
    """测试业务分析与其他智能体的协作"""
    flow = RequirementsFlow()
    analyst = flow.get_agent("analyst")
    clarifier = flow.get_agent("clarifier")

    # 模拟需求澄清结果
    requirement = "开发一个电子商务平台"
    clarified_requirement = await clarifier.clarify(requirement)

    # 基于澄清结果进行业务分析
    analysis_result = await analyst.analyze(clarified_requirement)

    # 验证数据共享
    assert (
        flow.collaboration_manager.get_shared_data("clarified_requirement") is not None
    )
    assert flow.collaboration_manager.get_shared_data("process_analysis") is not None

    # 验证状态更新
    analyst_state = flow.collaboration_manager.get_state(analyst.id)
    assert analyst_state.state == AgentState.COMPLETED
    assert analyst_state.progress == 1.0


@pytest.mark.asyncio
async def test_business_analysis_incremental():
    """测试业务分析的增量分析能力"""
    flow = RequirementsFlow()
    analyst = flow.get_agent("analyst")

    # 第一轮分析
    initial_requirement = "开发一个在线教育平台"
    initial_result = await analyst.analyze(initial_requirement)

    # 记录初始分析结果
    initial_process = flow.collaboration_manager.get_shared_data("process_analysis")
    initial_rules = flow.collaboration_manager.get_shared_data("business_rules")

    # 第二轮分析（补充需求）
    updated_requirement = initial_requirement + "\n增加直播课程和在线考试功能"
    updated_result = await analyst.analyze(updated_requirement)

    # 验证分析历史
    assert len(analyst.analysis_history) > 0
    latest_analysis = analyst.analysis_history[-1]
    assert latest_analysis["type"] == "final_report"

    # 验证更新后的共享数据
    updated_process = flow.collaboration_manager.get_shared_data("process_analysis")
    updated_rules = flow.collaboration_manager.get_shared_data("business_rules")

    assert updated_process != initial_process
    assert len(updated_rules) > len(initial_rules)
