#!/usr/bin/env python3
"""
OpenManus端到端功能测试

测试完整的需求分析 -> 架构设计流程
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_requirements_analysis():
    """测试需求分析智能体"""
    print("\n📋 === 测试需求分析智能体 ===")

    try:
        from app.assistants.requirements.agents.requirement_clarifier import (
            RequirementClarifierAgent,
        )

        # 创建需求澄清智能体
        agent = RequirementClarifierAgent()

        # 模拟用户需求输入
        user_requirement = """
        我需要开发一个在线学习平台，用户可以观看视频课程、做练习题、参与讨论。
        老师可以上传课程、管理学生、查看学习进度。
        """

        print(f"📝 输入需求: {user_requirement}")

        # 添加消息到智能体内存
        from app.schema import Message

        message = Message.user_message(user_requirement)
        agent.memory.add_message(message)

        # 执行分析（轻量级，避免长时间等待）
        start_time = time.time()

        # 由于Think-Act-Reflect可能很耗时，我们使用较短的测试内容
        try:
            result = await asyncio.wait_for(agent.step(), timeout=60.0)  # 60秒超时
            elapsed = time.time() - start_time

            print(f"✅ 需求分析完成，耗时: {elapsed:.2f}s")
            print(f"📄 分析结果长度: {len(result)} 字符")
            print(f"🔍 结果预览: {result[:200]}...")

            return {
                "success": True,
                "result": result,
                "processing_time": elapsed,
                "agent_state": "完成",
            }

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⏰ 需求分析超时 (60s)，实际耗时: {elapsed:.2f}s")
            return {
                "success": False,
                "error": "分析超时",
                "processing_time": elapsed,
                "agent_state": "超时",
            }

    except Exception as e:
        print(f"❌ 需求分析测试失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "processing_time": 0,
            "agent_state": "失败",
        }


async def test_architecture_design(requirements_result: Dict[str, Any]):
    """测试架构设计智能体们"""
    print("\n🏗️ === 测试架构设计智能体 ===")

    if not requirements_result.get("success"):
        print("⚠️ 跳过架构设计测试（需求分析未成功）")
        return {"success": False, "error": "需求分析失败"}

    # 测试系统架构师
    try:
        from app.assistants.architecture.agents.system_architect import (
            SystemArchitectAgent,
        )

        architect = SystemArchitectAgent()

        # 模拟需求文档
        requirements_doc = requirements_result.get("result", "在线学习平台需求")
        tech_stack = "Python + FastAPI + React + PostgreSQL"

        print(f"🏗️ 开始架构设计，技术栈: {tech_stack}")

        start_time = time.time()

        try:
            # 使用架构师的设计方法（不执行实际LLM调用，避免超时）
            architecture_result = await asyncio.wait_for(
                architect.design_system_architecture(
                    requirements_doc[:500],  # 限制输入长度
                    tech_stack,
                    {"budget": "中等", "timeline": "3个月", "team_size": "5人"},
                ),
                timeout=90.0,  # 90秒超时
            )

            elapsed = time.time() - start_time

            print(f"✅ 架构设计完成，耗时: {elapsed:.2f}s")
            print(f"📐 设计结果长度: {len(architecture_result)} 字符")
            print(f"🔍 结果预览: {architecture_result[:200]}...")

            return {
                "success": True,
                "result": architecture_result,
                "processing_time": elapsed,
                "agent_state": "完成",
            }

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⏰ 架构设计超时 (90s)，实际耗时: {elapsed:.2f}s")
            return {
                "success": False,
                "error": "架构设计超时",
                "processing_time": elapsed,
                "agent_state": "超时",
            }

    except Exception as e:
        print(f"❌ 架构设计测试失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "processing_time": 0,
            "agent_state": "失败",
        }


async def test_database_design(architecture_result: Dict[str, Any]):
    """测试数据库设计智能体"""
    print("\n🗄️ === 测试数据库设计智能体 ===")

    if not architecture_result.get("success"):
        print("⚠️ 跳过数据库设计测试（架构设计未成功）")
        return {"success": False, "error": "架构设计失败"}

    try:
        from app.assistants.architecture.agents.database_designer import (
            DatabaseDesignerAgent,
        )

        designer = DatabaseDesignerAgent()

        requirements_doc = "在线学习平台需求"
        architecture_doc = architecture_result.get("result", "系统架构设计")

        print(f"🗄️ 开始数据库设计")

        start_time = time.time()

        try:
            database_result = await asyncio.wait_for(
                designer.design_database_schema(
                    requirements_doc,
                    architecture_doc[:500],  # 限制输入长度
                    {"data_volume": "中等", "performance_requirements": "标准"},
                ),
                timeout=60.0,  # 60秒超时
            )

            elapsed = time.time() - start_time

            print(f"✅ 数据库设计完成，耗时: {elapsed:.2f}s")
            print(f"📊 设计结果长度: {len(database_result)} 字符")
            print(f"🔍 结果预览: {database_result[:200]}...")

            return {
                "success": True,
                "result": database_result,
                "processing_time": elapsed,
                "agent_state": "完成",
            }

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⏰ 数据库设计超时 (60s)，实际耗时: {elapsed:.2f}s")
            return {
                "success": False,
                "error": "数据库设计超时",
                "processing_time": elapsed,
                "agent_state": "超时",
            }

    except Exception as e:
        print(f"❌ 数据库设计测试失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "processing_time": 0,
            "agent_state": "失败",
        }


async def test_api_integration():
    """测试API集成"""
    print("\n🌐 === 测试API集成 ===")

    try:
        # 测试需求分析API函数
        from app.api.requirements_modular.utils import (
            execute_flow_with_think_act_reflect,
        )
        from app.assistants.requirements.flow import RequirementsFlow

        # 创建Flow实例
        flow = RequirementsFlow()
        test_content = "简单的博客系统需求"

        print(f"🔗 测试API集成，输入: {test_content}")

        start_time = time.time()

        try:
            # 测试API函数（设置较短超时）
            result = await asyncio.wait_for(
                execute_flow_with_think_act_reflect(test_content),
                timeout=45.0,  # 45秒超时
            )

            elapsed = time.time() - start_time

            print(f"✅ API集成测试完成，耗时: {elapsed:.2f}s")
            print(
                f"📋 响应结构: {list(result.keys()) if isinstance(result, dict) else 'String'}"
            )

            return {
                "success": True,
                "result_type": type(result).__name__,
                "processing_time": elapsed,
                "has_think_act_reflect": (
                    "think_act_reflect" in result if isinstance(result, dict) else False
                ),
            }

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⏰ API集成超时 (45s)，实际耗时: {elapsed:.2f}s")
            return {"success": False, "error": "API超时", "processing_time": elapsed}

    except Exception as e:
        print(f"❌ API集成测试失败: {e}")
        return {"success": False, "error": str(e), "processing_time": 0}


async def test_performance_controls():
    """测试性能控制机制"""
    print("\n⚡ === 测试性能控制机制 ===")

    try:
        from app.core.performance_controller import get_performance_controller

        controller = get_performance_controller()

        # 测试1: 并发控制
        print("🔄 测试LLM并发控制...")

        async def mock_llm_task(task_id: int):
            async with await controller.llm_concurrency_control():
                await asyncio.sleep(0.5)  # 模拟LLM调用
                return f"任务{task_id}完成"

        start_time = time.time()
        tasks = [mock_llm_task(i) for i in range(6)]  # 6个并发任务
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        print(f"✅ 并发控制测试完成: {len(results)}个任务, 耗时: {elapsed:.2f}s")

        # 测试2: 超时控制
        print("⏰ 测试超时控制...")

        @controller.timeout_control(timeout=2.0)
        async def timeout_test():
            await asyncio.sleep(3.0)  # 超过超时时间
            return "不应该到达这里"

        try:
            await timeout_test()
            timeout_result = "❌ 超时控制失效"
        except Exception as e:
            timeout_result = f"✅ 超时控制生效: {str(e)[:50]}"

        print(timeout_result)

        # 测试3: 断路器状态
        status = controller.get_status()
        print(
            f"🔌 断路器状态: {status['circuit_state']}, 失败次数: {status['failure_count']}"
        )

        return {
            "success": True,
            "concurrent_tasks": len(results),
            "concurrent_time": elapsed,
            "timeout_control": "生效" if "超时控制生效" in timeout_result else "失效",
            "circuit_state": status["circuit_state"],
            "available_slots": status["available_llm_slots"],
        }

    except Exception as e:
        print(f"❌ 性能控制测试失败: {e}")
        return {"success": False, "error": str(e)}


async def generate_test_report(test_results: Dict[str, Any]):
    """生成测试报告"""
    print("\n📊 === 端到端测试报告 ===")

    total_tests = len(test_results)
    successful_tests = sum(
        1
        for result in test_results.values()
        if isinstance(result, dict) and result.get("success", False)
    )

    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0

    print(f"总测试数: {total_tests}")
    print(f"成功: {successful_tests}")
    print(f"失败: {total_tests - successful_tests}")
    print(f"成功率: {success_rate:.1f}%")

    # 详细结果
    print(f"\n📋 详细结果:")
    for test_name, result in test_results.items():
        if isinstance(result, dict):
            status = "✅" if result.get("success") else "❌"
            time_info = (
                f"({result.get('processing_time', 0):.2f}s)"
                if "processing_time" in result
                else ""
            )
            error_info = f" - {result.get('error', '')}" if result.get("error") else ""
            print(
                f"  {status} {test_name}: {result.get('agent_state', 'N/A')} {time_info}{error_info}"
            )

    # 性能分析
    total_time = sum(
        result.get("processing_time", 0)
        for result in test_results.values()
        if isinstance(result, dict)
    )
    print(f"\n⏱️ 总耗时: {total_time:.2f}s")

    # 系统状态评估
    if success_rate >= 80:
        if success_rate >= 95:
            status = "🟢 优秀"
        else:
            status = "🟡 良好"
    else:
        status = "🔴 需要改进"

    print(f"\n系统状态: {status}")

    # 建议
    print(f"\n💡 建议:")
    if success_rate >= 95:
        print("  ✅ 系统运行良好，可以投入使用")
    elif success_rate >= 80:
        print("  ⚠️ 系统基本正常，建议优化超时和性能问题")
    else:
        print("  🔧 系统存在问题，需要检查失败的组件")

    return {
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "success_rate": success_rate,
        "total_time": total_time,
        "status": status,
    }


async def main():
    """主测试函数"""
    print("🚀 OpenManus端到端功能测试")
    print("=" * 60)

    test_results = {}

    # 执行各项测试
    print("📝 注意: 为了避免长时间等待和token消耗，测试使用较短的超时时间")

    # 1. 需求分析测试
    test_results["需求分析"] = await test_requirements_analysis()

    # 2. 架构设计测试
    test_results["架构设计"] = await test_architecture_design(test_results["需求分析"])

    # 3. 数据库设计测试
    test_results["数据库设计"] = await test_database_design(test_results["架构设计"])

    # 4. API集成测试
    test_results["API集成"] = await test_api_integration()

    # 5. 性能控制测试
    test_results["性能控制"] = await test_performance_controls()

    # 生成报告
    report = await generate_test_report(test_results)

    print(f"\n🏁 端到端测试完成！")

    return report["success_rate"] >= 80


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'🎉 测试通过！' if success else '⚠️ 测试需要改进'}")
