"""
测试冲突检测和差异处理系统

验证知识库和代码库集成的有效性
"""

import asyncio
import json
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.conflict_resolution_engine import ConflictResolutionEngine
from app.core.quality_driven_clarification_engine import (
    QualityDrivenClarificationEngine,
)
from app.logger import logger


async def test_conflict_detection():
    """测试冲突检测功能"""

    print("🔍 开始测试知识库和代码库冲突检测系统...")

    # 初始化引擎
    quality_engine = QualityDrivenClarificationEngine()
    conflict_engine = ConflictResolutionEngine()

    # 测试用例：包含多种潜在冲突的需求
    test_requirements = [
        {
            "name": "安全冲突需求",
            "content": "我需要一个用户管理系统，用户密码要明文存储在数据库中，方便管理员查看和重置。同时需要支持单点登录功能。",
            "expected_conflicts": ["安全冲突", "最佳实践违反"],
        },
        {
            "name": "架构冲突需求",
            "content": "希望开发一个区块链钱包系统，使用中心化数据库存储所有交易记录，并且要求系统支持离线交易处理。",
            "expected_conflicts": ["架构原则冲突", "技术不兼容"],
        },
        {
            "name": "技术选型差异",
            "content": "需要开发一个AI聊天机器人，使用PHP后端和jQuery前端，要求支持实时语音识别和自然语言处理。",
            "expected_conflicts": ["技术栈不匹配", "性能限制"],
        },
        {
            "name": "创新需求（合理差异）",
            "content": "希望在现有的需求分析系统中集成AI代码生成功能，用户输入需求后自动生成可运行的代码原型。",
            "expected_conflicts": ["无严重冲突", "创新机会"],
        },
    ]

    results = []

    for i, test_case in enumerate(test_requirements, 1):
        print(f"\n📝 测试用例 {i}: {test_case['name']}")
        print(f"需求内容: {test_case['content']}")

        try:
            # 进行冲突分析
            conflict_analysis = (
                await quality_engine.analyze_knowledge_and_code_conflicts(
                    test_case["content"], {}  # 质量分析结果暂时为空
                )
            )

            # 提取冲突信息
            knowledge_conflicts = conflict_analysis.get("knowledge_conflicts", {})
            codebase_conflicts = conflict_analysis.get("codebase_conflicts", {})
            critical_conflicts = conflict_analysis.get("critical_conflicts", [])
            manageable_differences = conflict_analysis.get("manageable_differences", [])
            conflict_level = conflict_analysis.get("overall_conflict_level", "unknown")

            print(f"🔍 冲突级别: {conflict_level}")
            print(f"🚨 严重冲突: {len(critical_conflicts)} 个")
            print(f"🤝 可协商差异: {len(manageable_differences)} 个")

            # 显示具体冲突
            if critical_conflicts:
                print("严重冲突详情:")
                for conflict in critical_conflicts[:3]:  # 只显示前3个
                    print(
                        f"  - {conflict.get('category', '')}: {conflict.get('description', '')[:100]}"
                    )

            if manageable_differences:
                print("可协商差异:")
                for diff in manageable_differences[:2]:  # 只显示前2个
                    print(
                        f"  - {diff.get('category', '')}: {diff.get('description', '')[:100]}"
                    )

            # 使用冲突解决引擎生成处理建议
            if knowledge_conflicts or codebase_conflicts:
                resolution_plan = await conflict_engine.analyze_conflicts_comprehensive(
                    test_case["content"], knowledge_conflicts, codebase_conflicts
                )

                print(
                    f"📋 解决方案评分: {resolution_plan.overall_resolution_score:.2f}"
                )
                print(f"🎯 推荐策略数量: {len(resolution_plan.strategies)}")

                if resolution_plan.stakeholder_decisions_required:
                    print("🤝 需要利益相关者决策:")
                    for decision in resolution_plan.stakeholder_decisions_required[:2]:
                        print(f"  - {decision}")

                # 显示实施路线图
                roadmap = resolution_plan.implementation_roadmap
                if roadmap.get("immediate_actions"):
                    print("⚡ 立即行动:")
                    for action in roadmap["immediate_actions"][:2]:
                        print(f"  - {action[:80]}")

            # 记录结果
            result = {
                "test_case": test_case["name"],
                "conflict_level": conflict_level,
                "critical_count": len(critical_conflicts),
                "manageable_count": len(manageable_differences),
                "has_stakeholder_decisions": bool(
                    conflict_analysis.get("requires_stakeholder_decision", False)
                ),
                "resolution_score": (
                    resolution_plan.overall_resolution_score
                    if "resolution_plan" in locals()
                    else 0
                ),
            }
            results.append(result)

            print("✅ 测试完成")

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append({"test_case": test_case["name"], "error": str(e)})

    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 冲突检测系统测试总结")
    print("=" * 60)

    success_count = len([r for r in results if "error" not in r])
    print(f"✅ 成功测试: {success_count}/{len(test_requirements)}")

    # 分析冲突检测效果
    critical_detected = len([r for r in results if r.get("critical_count", 0) > 0])
    manageable_detected = len([r for r in results if r.get("manageable_count", 0) > 0])

    print(f"🚨 检测到严重冲突的案例: {critical_detected}")
    print(f"🤝 检测到可协商差异的案例: {manageable_detected}")

    stakeholder_required = len(
        [r for r in results if r.get("has_stakeholder_decisions")]
    )
    print(f"🤝 需要利益相关者决策的案例: {stakeholder_required}")

    avg_resolution_score = (
        sum(r.get("resolution_score", 0) for r in results) / len(results)
        if results
        else 0
    )
    print(f"📈 平均解决方案评分: {avg_resolution_score:.2f}")

    # 保存详细结果
    with open("conflict_detection_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📁 详细结果已保存到: conflict_detection_test_results.json")

    return results


async def test_difference_classification():
    """测试差异分类功能"""

    print("\n🔍 测试差异分类功能...")

    conflict_engine = ConflictResolutionEngine()

    test_scenarios = [
        {
            "description": "用户密码需要明文存储以便管理",
            "context": "用户管理系统",
            "expected_nature": "incompatible",  # 安全冲突
        },
        {
            "description": "建议使用React替代现有的Vue框架",
            "context": "前端开发",
            "expected_nature": "negotiable",  # 技术选型差异
        },
        {
            "description": "集成AI智能推荐功能提升用户体验",
            "context": "电商平台",
            "expected_nature": "innovation",  # 创新机会
        },
    ]

    for scenario in test_scenarios:
        nature = conflict_engine.classify_difference_nature(
            scenario["description"], scenario["context"]
        )

        print(f"📝 冲突描述: {scenario['description']}")
        print(f"🎯 分类结果: {nature.value}")
        print(f"✅ 预期分类: {scenario['expected_nature']}")
        print(
            f"{'✅ 正确' if nature.value == scenario['expected_nature'] else '❌ 不正确'}"
        )
        print()


if __name__ == "__main__":
    asyncio.run(test_conflict_detection())
    asyncio.run(test_difference_classification())
