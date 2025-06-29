#!/usr/bin/env python3
"""
快速测试脚本

用于快速测试OpenManus的核心功能
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List

from app.api.requirements_modular.utils import execute_flow_with_think_act_reflect
from app.assistants.requirements.flow import RequirementsFlow
from app.core.adaptive_learning_system import AnalysisCase
from app.core.performance_controller import get_performance_controller
from app.logger import logger


async def test_think_act_reflect():
    """测试Think-Act-Reflect流程"""
    try:
        # 执行测试
        result = await execute_flow_with_think_act_reflect(
            "需要一个简单的待办事项管理系统"
        )

        # 验证结果
        if not isinstance(result, dict):
            raise ValueError("返回结果格式错误")

        print("✅ Think-Act-Reflect测试通过")
        return True

    except Exception as e:
        print(f"❌ Think-Act-Reflect测试失败: {e}")
        return False


async def test_performance_controller():
    """测试性能控制器"""
    try:
        controller = get_performance_controller()
        status = controller.get_status()

        print(f"✅ 性能控制器状态: {json.dumps(status, indent=2)}")
        return True

    except Exception as e:
        print(f"❌ 性能控制器测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 开始快速测试...")

    # 记录开始时间
    start_time = time.time()

    # 运行测试
    results = await asyncio.gather(
        test_think_act_reflect(),
        test_performance_controller(),
    )

    # 检查结果
    success = all(results)
    duration = time.time() - start_time

    print(f"\n⏱️  测试耗时: {duration:.2f}秒")
    print(f"📊 测试结果: {'✅ 全部通过' if success else '❌ 存在失败'}")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
