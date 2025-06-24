"""
简化版冲突检测测试 - 专注核心功能验证
"""

import asyncio
import json
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.quality_driven_clarification_engine import (
    QualityDrivenClarificationEngine,
)
from app.logger import logger


async def test_simple_conflict_detection():
    """简化版冲突检测测试"""

    print("🔍 开始简化版冲突检测测试...")

    # 初始化引擎
    quality_engine = QualityDrivenClarificationEngine()

    # 简单测试用例
    test_requirements = [
        {
            "name": "正常需求",
            "content": "我需要一个学生成绩管理系统，包含学生信息管理、成绩录入、成绩查询等功能。",
        },
        {
            "name": "安全问题需求",
            "content": "我需要一个用户管理系统，用户密码要明文存储，方便管理员查看。",
        },
    ]

    for i, test_case in enumerate(test_requirements, 1):
        print(f"\n📝 测试用例 {i}: {test_case['name']}")
        print(f"需求内容: {test_case['content']}")

        try:
            # 进行冲突分析
            conflict_analysis = (
                await quality_engine.analyze_knowledge_and_code_conflicts(
                    test_case["content"], {}
                )
            )

            # 提取结果
            conflict_level = conflict_analysis.get("overall_conflict_level", "unknown")
            critical_conflicts = conflict_analysis.get("critical_conflicts", [])
            manageable_differences = conflict_analysis.get("manageable_differences", [])

            print(f"🔍 冲突级别: {conflict_level}")
            print(f"🚨 严重冲突: {len(critical_conflicts)} 个")
            print(f"🤝 可协商差异: {len(manageable_differences)} 个")

            # 显示冲突建议
            suggestions = conflict_analysis.get("conflict_resolution_suggestions", [])
            if suggestions:
                print("💡 处理建议:")
                for suggestion in suggestions[:3]:
                    print(f"  - {suggestion}")

            print("✅ 测试完成")

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()

    print("\n🎉 简化版冲突检测测试完成！")


if __name__ == "__main__":
    asyncio.run(test_simple_conflict_detection())
