"""
需求分析工作流测试
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.workflow.core.workflow_error import WorkflowError
from app.workflow.engine.event_bus import EventBus
from app.workflow.engine.state_store import StateStore
from app.workflow.engine.workflow_engine import WorkflowEngine
from app.workflow.flows.requirements_workflow import RequirementsWorkflow


@pytest.fixture
async def workflow_engine():
    """工作流引擎测试夹具"""
    state_store = StateStore(redis_url="redis://localhost:6379/0")
    event_bus = EventBus()
    engine = WorkflowEngine(state_store=state_store, event_bus=event_bus)
    await state_store.connect()
    yield engine
    await state_store.disconnect()


@pytest.fixture
def requirements_workflow():
    """需求分析工作流测试夹具"""
    return RequirementsWorkflow()


@pytest.mark.asyncio
async def test_workflow_registration(workflow_engine, requirements_workflow):
    """测试工作流注册"""
    # 注册工作流
    await workflow_engine.register_workflow(requirements_workflow)

    # 验证工作流已注册
    assert requirements_workflow.id in workflow_engine._workflows

    # 验证工作流定义
    registered_workflow = workflow_engine._workflows[requirements_workflow.id]
    assert registered_workflow.name == "需求分析工作流"
    assert len(registered_workflow.steps) == 5  # 5个基本步骤


@pytest.mark.asyncio
async def test_workflow_execution(workflow_engine, requirements_workflow):
    """测试工作流执行"""
    # 注册工作流
    await workflow_engine.register_workflow(requirements_workflow)

    # 准备测试数据
    input_data = {
        "user_input": "我需要一个在线商城系统，支持用户注册、商品浏览、购物车和订单管理等基本功能。"
    }

    # 执行工作流
    result = await workflow_engine.execute_workflow(
        requirements_workflow.id, input_data
    )

    # 验证执行结果
    assert result.status == "completed"
    assert "requirements_document" in result.data
    assert result.error is None
    assert isinstance(result.duration, float)


@pytest.mark.asyncio
async def test_workflow_error_handling(workflow_engine, requirements_workflow):
    """测试工作流错误处理"""
    # 注册工作流
    await workflow_engine.register_workflow(requirements_workflow)

    # 准备测试数据（缺少必需输入）
    input_data = {}

    # 执行工作流（应该失败）
    with pytest.raises(WorkflowError) as exc_info:
        await workflow_engine.execute_workflow(requirements_workflow.id, input_data)

    assert "缺少必需的输入" in str(exc_info.value)


@pytest.mark.asyncio
async def test_workflow_state_management(workflow_engine, requirements_workflow):
    """测试工作流状态管理"""
    # 注册工作流
    await workflow_engine.register_workflow(requirements_workflow)

    # 准备测试数据
    input_data = {"user_input": "测试需求"}

    # 执行工作流
    result = await workflow_engine.execute_workflow(
        requirements_workflow.id, input_data
    )

    # 验证状态存储
    state, version = await workflow_engine.state_store.load_workflow_state(
        result.execution_id
    )

    assert state is not None
    assert state["status"] == "completed"
    assert state["workflow_id"] == requirements_workflow.id


@pytest.mark.asyncio
async def test_workflow_event_handling(workflow_engine, requirements_workflow):
    """测试工作流事件处理"""
    events = []

    async def event_handler(event):
        events.append(event)

    # 订阅事件
    await workflow_engine.event_bus.subscribe("workflow_started", event_handler)
    await workflow_engine.event_bus.subscribe("workflow_completed", event_handler)

    # 注册工作流
    await workflow_engine.register_workflow(requirements_workflow)

    # 准备测试数据
    input_data = {"user_input": "测试需求"}

    # 执行工作流
    await workflow_engine.execute_workflow(requirements_workflow.id, input_data)

    # 验证事件
    assert len(events) == 2
    assert events[0].type == "workflow_started"
    assert events[1].type == "workflow_completed"


@pytest.mark.asyncio
async def test_workflow_quality_review(workflow_engine, requirements_workflow):
    """测试需求文档质量审查"""
    # 注册工作流
    await workflow_engine.register_workflow(requirements_workflow)

    # 准备测试数据
    input_data = {"user_input": "测试需求"}

    # Mock质量审查结果
    quality_report = {
        "score": 0.7,  # 低于80%阈值
        "issues": ["文档不完整", "缺少测试用例"],
    }
    revision_suggestions = ["添加更详细的功能描述", "补充测试用例"]

    # 执行工作流
    result = await workflow_engine.execute_workflow(
        requirements_workflow.id, input_data
    )

    # 验证是否添加了修改步骤
    workflow = workflow_engine._workflows[requirements_workflow.id]
    assert len(workflow.steps) == 6  # 5个基本步骤 + 1个修改步骤
    assert workflow.steps[-1].name == "文档修改"
