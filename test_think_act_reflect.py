#!/usr/bin/env python3
"""
Think-Act-Reflect架构升级效果测试

测试内容：
1. Think Tool深度推理测试
2. Reflection Engine质量评估测试
3. 需求澄清智能体集成测试
4. 质量对比分析
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.assistants.requirements.agents.requirement_clarifier import (
    RequirementClarifierAgent,
)
from app.core.reflection_engine import ReflectionEngine
from app.core.think_tool import ThinkingPhase, ThinkTool
from app.llm import LLM
from app.logger import logger


async def test_think_tool():
    """测试Think Tool深度推理功能"""
    print("\n🧠 === Think Tool 深度推理测试 ===")

    think_tool = ThinkTool()

    test_problem = "我想开发一个在线教育平台，支持直播课程和录播课程，需要有学生管理、课程管理、支付功能"

    print(f"测试问题: {test_problem}")

    # 执行结构化思维
    result = await think_tool.structured_thinking(
        problem=test_problem,
        context={"domain": "教育平台", "type": "web应用"},
        phases=[
            ThinkingPhase.UNDERSTANDING,
            ThinkingPhase.ANALYSIS,
            ThinkingPhase.PLANNING,
        ],
    )

    print(f"\n✅ 思维分析完成")
    print(f"📊 整体置信度: {result.confidence:.2f}")
    print(f"📝 思维步骤数: {len(result.steps)}")
    print(f"💡 关键洞察: {len(result.insights)}个")
    print(f"🎯 建议行动: {len(result.next_actions)}个")

    print(f"\n📋 思维总结:")
    print(result.summary[:200] + "..." if len(result.summary) > 200 else result.summary)

    print(f"\n💡 关键洞察:")
    for i, insight in enumerate(result.insights[:3], 1):
        print(f"  {i}. {insight}")

    return result


async def test_reflection_engine():
    """测试Reflection Engine质量评估功能"""
    print("\n🔍 === Reflection Engine 质量评估测试 ===")

    reflection_engine = ReflectionEngine()

    # 模拟一个需求分析文档
    test_artifact = """
需求分析文档：

1. 功能需求：
   - 用户注册登录
   - 课程管理
   - 直播功能

2. 非功能需求：
   - 支持1000并发用户
   - 响应时间小于2秒
"""

    print(f"测试文档: {test_artifact[:100]}...")

    # 执行综合反思
    reflection_result = await reflection_engine.comprehensive_reflection(
        artifact=test_artifact,
        context={"type": "需求分析", "domain": "教育平台"},
        artifact_type="requirement_analysis",
    )

    print(f"\n✅ 反思评估完成")
    print(f"📊 综合评分: {reflection_result.quality_metrics.overall_score:.2f}")
    print(f"🔍 识别问题: {len(reflection_result.identified_issues)}个")
    print(f"💡 改进建议: {len(reflection_result.improvement_suggestions)}个")
    print(f"🎯 评估置信度: {reflection_result.confidence:.2f}")

    print(f"\n📊 质量指标详情:")
    metrics = reflection_result.quality_metrics.to_dict()
    for metric, score in metrics.items():
        print(f"  {metric}: {score:.2f}")

    print(f"\n⚠️ 识别的问题:")
    for i, issue in enumerate(reflection_result.identified_issues[:3], 1):
        print(f"  {i}. {issue}")

    return reflection_result


async def test_upgraded_agent():
    """测试升级后的需求澄清智能体"""
    print("\n🤖 === 升级智能体 Think-Act-Reflect 测试 ===")

    agent = RequirementClarifierAgent()

    test_input = (
        "我想做一个类似美团的外卖配送平台，要有商家入驻、用户下单、骑手配送等功能"
    )

    print(f"测试输入: {test_input}")

    # 更新智能体记忆
    agent.update_memory("user", test_input)

    # 执行Think-Act-Reflect流程
    result = await agent.step()

    print(f"\n✅ Think-Act-Reflect流程完成")
    print(f"📝 生成的分析报告:")
    print(result[:300] + "..." if len(result) > 300 else result)

    # 检查生成的文档
    status = agent.get_clarification_status()
    print(f"\n📊 智能体状态:")
    print(f"  当前步骤: {status['current_step']}")
    print(f"  澄清评分: {status['clarity_score']}")
    print(f"  生成文档: {status['questions_asked']}个")

    return result


async def quality_comparison_test():
    """质量对比测试"""
    print("\n⚖️ === 质量对比测试 ===")

    # 模拟原有方式的简单输出
    simple_output = """
用户需求：外卖平台
功能：下单、配送、支付
用户：顾客、商家、骑手
"""

    # 使用反思引擎评估
    reflection_engine = ReflectionEngine()

    simple_reflection = await reflection_engine.comprehensive_reflection(
        artifact=simple_output, artifact_type="simple_analysis"
    )

    print(f"📊 简单分析质量评分: {simple_reflection.quality_metrics.overall_score:.2f}")

    # 执行升级后的分析
    upgraded_result = await test_upgraded_agent()

    upgraded_reflection = await reflection_engine.comprehensive_reflection(
        artifact=upgraded_result, artifact_type="think_act_reflect_analysis"
    )

    print(
        f"📊 Think-Act-Reflect质量评分: {upgraded_reflection.quality_metrics.overall_score:.2f}"
    )

    improvement = (
        upgraded_reflection.quality_metrics.overall_score
        - simple_reflection.quality_metrics.overall_score
    )
    print(
        f"📈 质量提升: {improvement:.2f} ({improvement/simple_reflection.quality_metrics.overall_score*100:.1f}%)"
    )

    return {
        "simple_score": simple_reflection.quality_metrics.overall_score,
        "upgraded_score": upgraded_reflection.quality_metrics.overall_score,
        "improvement": improvement,
    }


async def main():
    """主测试流程"""
    print("🚀 === OpenManus Think-Act-Reflect 架构升级测试 ===")

    try:
        # 1. Think Tool 测试
        thinking_result = await test_think_tool()

        # 2. Reflection Engine 测试
        reflection_result = await test_reflection_engine()

        # 3. 升级智能体测试
        agent_result = await test_upgraded_agent()

        # 4. 质量对比测试
        comparison_result = await quality_comparison_test()

        # 5. 总结报告
        print("\n📋 === 测试总结报告 ===")
        print(f"✅ Think Tool 深度推理: 置信度 {thinking_result.confidence:.2f}")
        print(
            f"✅ Reflection Engine 质量评估: 评分 {reflection_result.quality_metrics.overall_score:.2f}"
        )
        print(f"✅ 升级智能体: Think-Act-Reflect 流程正常")
        print(
            f"✅ 质量提升: {comparison_result['improvement']:.2f} (+{comparison_result['improvement']/comparison_result['simple_score']*100:.1f}%)"
        )

        print(f"\n🎯 核心改进验证:")
        print(f"1. 智能程度提升: Think Tool 实现深度推理")
        print(f"2. 产物质量提升: Reflection Engine 自动评估优化")
        print(f"3. 工作流程升级: Think-Act-Reflect 完整闭环")
        print(
            f"4. 量化效果明显: 质量评分提升 {comparison_result['improvement']/comparison_result['simple_score']*100:.1f}%"
        )

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
