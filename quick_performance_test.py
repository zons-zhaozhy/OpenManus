#!/usr/bin/env python3
"""
性能控制系统测试脚本

测试功能：
1. 超时控制
2. LLM并发限制
3. 断路器模式
4. 沙盒清理禁用
"""

import asyncio
import logging
import time

from app.assistants.requirements.agents.requirement_clarifier import (
    RequirementClarifierAgent,
)
from app.config import config
from app.core.performance_controller import PerformanceConfig, PerformanceController
from app.llm import LLM

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_timeout_control():
    """测试超时控制"""
    print("\n🕐 === 测试超时控制 ===")

    # 创建性能控制器（短超时用于测试）
    test_config = PerformanceConfig(
        global_timeout=5.0,  # 5秒超时用于测试
        llm_concurrent_limit=2,
        circuit_failure_threshold=2,
    )
    controller = PerformanceController(test_config)

    @controller.timeout_control()
    async def slow_task():
        print("开始执行慢任务...")
        await asyncio.sleep(10)  # 模拟10秒的慢任务
        return "任务完成"

    try:
        start_time = time.time()
        result = await slow_task()
        print(f"❌ 任务意外完成: {result}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✅ 任务超时控制生效: {e}, 耗时: {elapsed:.2f}s")


async def test_concurrent_control():
    """测试LLM并发控制"""
    print("\n🎛️ === 测试LLM并发控制 ===")

    controller = PerformanceController(PerformanceConfig(llm_concurrent_limit=2))

    async def mock_llm_call(call_id: int):
        async with await controller.llm_concurrency_control():
            print(f"LLM调用 {call_id} 开始执行")
            await asyncio.sleep(2)  # 模拟LLM调用
            print(f"LLM调用 {call_id} 完成")
            return f"调用{call_id}结果"

    # 同时发起4个调用，但最多只能2个并发
    start_time = time.time()
    tasks = [mock_llm_call(i) for i in range(4)]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time

    print(f"✅ 并发控制测试完成，耗时: {elapsed:.2f}s")
    print(f"   预期: 约4秒 (2批次×2秒), 实际: {elapsed:.2f}s")


async def test_circuit_breaker():
    """测试断路器模式"""
    print("\n⚡ === 测试断路器模式 ===")

    controller = PerformanceController(PerformanceConfig(circuit_failure_threshold=2))

    @controller.timeout_control(timeout=1.0)
    async def failing_task():
        await asyncio.sleep(2)  # 超时任务
        return "不应该到达这里"

    # 连续失败以触发断路器
    for i in range(3):
        try:
            await failing_task()
        except Exception as e:
            print(f"失败 {i+1}: {e}")

    # 现在断路器应该开启
    try:
        await controller.circuit_breaker_check("test_operation")
        print("❌ 断路器未生效")
    except Exception as e:
        print(f"✅ 断路器生效: {e}")


async def test_requirements_agent_timeout():
    """测试需求澄清智能体的超时控制"""
    print("\n🤖 === 测试需求澄清智能体超时控制 ===")

    try:
        agent = RequirementClarifierAgent()

        # 模拟简短需求分析（应该在120秒内完成）
        start_time = time.time()
        result = await agent.step()
        elapsed = time.time() - start_time

        print(f"✅ 智能体执行完成，耗时: {elapsed:.2f}s")
        print(f"结果长度: {len(result)} 字符")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"⚠️ 智能体执行异常: {e}, 耗时: {elapsed:.2f}s")


def test_sandbox_cleanup_disabled():
    """测试沙盒清理禁用"""
    print("\n🚫 === 测试沙盒清理禁用 ===")

    # 检查配置
    print(f"沙盒清理启用状态: {config.performance_config.enable_sandbox_cleanup}")

    if not config.performance_config.enable_sandbox_cleanup:
        print("✅ 沙盒自动清理已禁用")
    else:
        print("⚠️ 沙盒自动清理仍然启用")


async def test_performance_status():
    """测试性能控制状态"""
    print("\n📊 === 性能控制状态 ===")

    controller = PerformanceController()
    status = controller.get_status()

    for key, value in status.items():
        print(f"{key}: {value}")


async def main():
    """主测试函数"""
    print("🚀 OpenManus 性能控制系统测试")
    print("=" * 50)

    # 基础配置测试
    test_sandbox_cleanup_disabled()

    # 性能控制测试
    await test_performance_status()
    await test_timeout_control()
    await test_concurrent_control()
    await test_circuit_breaker()

    # 实际智能体测试（可选，因为可能消耗token）
    print("\n❓ 是否测试实际智能体执行？(y/N):")
    # 为了自动化测试，直接跳过用户输入
    # response = input().lower()
    response = "n"  # 默认不执行，避免token消耗

    if response == "y":
        await test_requirements_agent_timeout()
    else:
        print("⏭️ 跳过实际智能体测试（避免token消耗）")

    print("\n✅ 性能控制系统测试完成！")
    print("🎯 建议：如果所有测试通过，系统性能控制已正确实施")


if __name__ == "__main__":
    asyncio.run(main())
