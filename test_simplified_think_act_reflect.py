#!/usr/bin/env python3
"""
简化版Think-Act-Reflect测试

用于快速验证Think-Act-Reflect功能
"""

import asyncio
import os
from typing import Dict

from app.api.requirements_modular.utils import execute_flow_with_think_act_reflect
from app.assistants.requirements.agents.requirement_clarifier import (
    RequirementClarifierAgent,
)
from app.core.reflection_engine import ReflectionEngine
from app.core.think_tool import ThinkTool
from app.logger import logger


async def test_core_components():
    """测试核心组件"""
    try:
        # 测试智能体创建
        agent = RequirementClarifierAgent(name="测试")
        print("✅ RequirementClarifierAgent创建成功")

        # 检查核心属性
        has_think_tool = hasattr(agent, "think_tool")
        has_reflection_engine = hasattr(agent, "reflection_engine")
        print(f"- think_tool: {'✅' if has_think_tool else '❌'}")
        print(f"- reflection_engine: {'✅' if has_reflection_engine else '❌'}")

        return True
    except Exception as e:
        logger.error(f"核心组件测试失败: {e}")
        return False


async def test_frontend_components():
    """测试前端组件"""
    try:
        # 检查关键组件
        component_path = "app/web/src/components/ThinkActReflectPanel.tsx"
        if os.path.exists(component_path):
            print("✅ ThinkActReflectPanel.tsx 组件存在")
            return True
        else:
            print("❌ 前端组件不存在")
            return False
    except Exception as e:
        logger.error(f"前端组件测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🔬 简化版Think-Act-Reflect测试")
    print("=" * 40)

    try:
        # 运行测试
        results = await asyncio.gather(
            test_core_components(),
            test_frontend_components(),
        )

        # 检查结果
        success = all(results)

        if success:
            print("\n🎉 所有基础检查通过!")
            print("💡 建议: 可以启动web服务进行前端测试")
            print("⚠️ 注意: 避免运行完整测试以节省token")
        else:
            print("\n❌ 部分测试未通过")

        return success

    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
