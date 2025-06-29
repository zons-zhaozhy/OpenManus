"""
测试智能体协作管理器
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from app.assistants.requirements.collaboration_manager import CollaborationManager
from app.core.types import AgentState, Message
from app.metrics import MetricsCollector


class MockAgent:
    """模拟智能体"""

    def __init__(self, agent_id: str):
        self.id = agent_id


@pytest.fixture
async def collaboration_manager():
    """创建协作管理器实例"""
    manager = CollaborationManager()
    yield manager


@pytest.mark.asyncio
async def test_dependency_management():
    """测试依赖关系管理"""
    manager = CollaborationManager()

    # 注册智能体
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    await manager.register_agent(agent1)
    await manager.register_agent(agent2)

    # 添加依赖关系
    await manager.add_dependency(agent2.id, agent1.id)

    # 验证依赖关系
    assert agent1.id in manager._dependency_graph[agent2.id]
    assert agent1.id in manager.get_state(agent2.id).dependencies

    # 检查依赖状态
    assert not await manager.check_dependencies(agent2.id)

    # 更新依赖智能体状态
    await manager.update_state(agent1.id, AgentState.COMPLETED)
    assert await manager.check_dependencies(agent2.id)


@pytest.mark.asyncio
async def test_task_dependency_management():
    """测试任务依赖关系管理"""
    manager = CollaborationManager()

    # 添加任务依赖
    await manager.add_task_dependency("task2", "task1")

    # 验证任务依赖
    dependencies = manager.get_task_dependencies()
    assert "task1" in dependencies["task2"]


@pytest.mark.asyncio
async def test_performance_metrics():
    """测试性能指标收集"""
    manager = CollaborationManager()

    # 注册智能体
    agent = MockAgent("test_agent")
    await manager.register_agent(agent)

    # 发送消息
    message = Message(role="system", content="test message")
    await manager.send_message("sender", agent.id, message)

    # 更新状态
    await manager.update_state(agent.id, AgentState.RUNNING)
    await manager.update_state(agent.id, AgentState.COMPLETED)

    # 获取性能指标
    metrics = await manager.get_performance_metrics()

    # 验证指标
    assert "message_delivery" in metrics
    assert "state_transitions" in metrics
    assert "events" in metrics


@pytest.mark.asyncio
async def test_metrics_anomaly_detection():
    """测试指标异常检测"""
    metrics = MetricsCollector()

    # 记录正常指标
    for i in range(10):
        await metrics.record_metric("test_metric", 100 + i)

    # 记录异常指标（远离均值）
    await metrics.record_metric("test_metric", 1000)

    # 验证异常检测
    assert await metrics._is_anomaly("test_metric", 1000)
    assert not await metrics._is_anomaly("test_metric", 105)

    # 测试标准差接近0的情况
    for _ in range(10):
        await metrics.record_metric("constant_metric", 100)
    assert await metrics._is_anomaly("constant_metric", 102)
    assert not await metrics._is_anomaly("constant_metric", 100)

    # 测试动态阈值
    for i in range(30):
        await metrics.record_metric("large_dataset", 100 + i % 5)
    assert await metrics._is_anomaly("large_dataset", 200)
    assert not await metrics._is_anomaly("large_dataset", 102)


@pytest.mark.asyncio
async def test_metrics_statistics():
    """测试指标统计"""
    metrics = MetricsCollector()

    # 记录指标
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for value in values:
        await metrics.record_metric("test_metric", value)

    # 获取统计信息
    stats = await metrics.get_metric_statistics("test_metric")

    # 验证统计结果
    assert stats["min"] == 1
    assert stats["max"] == 10
    assert stats["avg"] == 5.5
    assert stats["count"] == 10
    assert "std" in stats
    assert "p50" in stats
    assert "p90" in stats
    assert "p95" in stats
    assert "p99" in stats


@pytest.mark.asyncio
async def test_metrics_cleanup():
    """测试指标清理"""
    metrics = MetricsCollector()

    # 记录指标
    old_time = datetime.now() - timedelta(days=2)
    new_time = datetime.now()

    await metrics.record_metric("test_metric", 1)
    await metrics.record_metric("test_metric", 2)

    # 清理旧数据
    await metrics.clear_old_metrics(new_time - timedelta(days=1))

    # 验证清理结果
    stats = await metrics.get_metric_statistics("test_metric")
    assert stats["count"] == 2  # 因为我们的测试数据都是新的


@pytest.mark.asyncio
async def test_concurrent_metrics_recording():
    """测试并发指标记录"""
    metrics = MetricsCollector()

    async def record_metrics():
        for i in range(100):
            await metrics.record_metric("concurrent_test", i)
            await asyncio.sleep(0.01)

    # 创建多个并发任务
    tasks = [record_metrics() for _ in range(5)]
    await asyncio.gather(*tasks)

    # 验证结果
    stats = await metrics.get_metric_statistics("concurrent_test")
    assert stats["count"] == 500  # 5个任务，每个100条记录


@pytest.mark.asyncio
async def test_metrics_by_label():
    """测试标签过滤"""
    metrics = MetricsCollector()

    # 记录带标签的指标
    await metrics.record_metric(
        "test_metric", 1, {"agent": "agent1", "type": "message"}
    )
    await metrics.record_metric(
        "test_metric", 2, {"agent": "agent2", "type": "message"}
    )

    # 按标签过滤
    filtered = await metrics.get_metrics_by_label("test_metric", "agent", "agent1")
    assert len(filtered) == 1
    assert filtered[0]["value"] == 1


@pytest.mark.asyncio
async def test_event_recording():
    """测试事件记录"""
    metrics = MetricsCollector()

    # 记录事件
    await metrics.record_event("test_event", {"agent": "agent1", "action": "start"})

    # 获取所有指标
    all_metrics = await metrics.get_all_metrics()

    # 验证事件
    assert len(all_metrics["events"]) == 1
    assert all_metrics["events"][0]["type"] == "test_event"


@pytest.mark.asyncio
async def test_collaboration_manager_integration():
    """测试协作管理器集成"""
    manager = CollaborationManager()

    # 注册智能体
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    await manager.register_agent(agent1)
    await manager.register_agent(agent2)

    # 添加依赖关系
    await manager.add_dependency(agent2.id, agent1.id)

    # 发送消息
    message = Message(role="system", content="test message")
    await manager.send_message(agent1.id, agent2.id, message)

    # 更新状态
    await manager.update_state(agent1.id, AgentState.RUNNING)
    await manager.share_data(agent1.id, "test_key", "test_value")
    await manager.update_state(agent1.id, AgentState.COMPLETED)

    # 获取性能指标
    metrics = await manager.get_performance_metrics()

    # 验证集成结果
    assert "message_delivery" in metrics
    assert "state_transitions" in metrics
    assert "data_sharing" in metrics
    assert await manager.check_dependencies(agent2.id)
    assert manager.get_shared_data("test_key") == "test_value"
