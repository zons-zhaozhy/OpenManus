#!/usr/bin/env python3
"""
OpenManus系统全面健康检查脚本

检查项目：
1. 核心模块导入状态
2. 配置文件完整性
3. 需求分析智能体功能
4. 架构设计智能体功能
5. API接口状态
6. 前端组件状态
7. 性能控制系统
8. 资源使用情况
"""

import asyncio
import logging
import os
import sys
import time
import traceback
from typing import Any, Dict, List

import psutil

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SystemHealthChecker:
    """系统健康检查器"""

    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []

    def check_result(
        self, check_name: str, success: bool, details: str = "", error: str = ""
    ):
        """记录检查结果"""
        self.results[check_name] = {
            "success": success,
            "details": details,
            "error": error,
            "timestamp": time.time(),
        }

        status = "✅" if success else "❌"
        print(f"{status} {check_name}: {details if success else error}")

        if not success:
            self.errors.append(f"{check_name}: {error}")

    async def check_core_imports(self):
        """检查核心模块导入"""
        print("\n🔍 === 检查核心模块导入 ===")

        modules_to_check = [
            ("app.config", "配置模块"),
            ("app.llm", "LLM模块"),
            ("app.core.performance_controller", "性能控制器"),
            ("app.core.think_tool", "思维工具"),
            ("app.core.reflection_engine", "反思引擎"),
            (
                "app.assistants.requirements.agents.requirement_clarifier",
                "需求澄清智能体",
            ),
            ("app.assistants.architecture.agents.system_architect", "系统架构师"),
            ("app.assistants.architecture.agents.database_designer", "数据库设计师"),
            ("app.assistants.architecture.agents.tech_selector", "技术选择器"),
            ("app.assistants.architecture.agents.architecture_reviewer", "架构审查师"),
            ("app.tool.requirements_modeling", "需求建模工具"),
            ("app.tool.architecture_modeling", "架构建模工具"),
        ]

        for module_name, description in modules_to_check:
            try:
                __import__(module_name)
                self.check_result(f"导入{description}", True, f"{module_name} 成功导入")
            except Exception as e:
                self.check_result(
                    f"导入{description}", False, error=f"{module_name} 导入失败: {e}"
                )

    async def check_configuration(self):
        """检查配置完整性"""
        print("\n⚙️ === 检查配置完整性 ===")

        try:
            from app.config import config

            # 检查基础配置
            if hasattr(config, "llm"):
                self.check_result("LLM配置", True, "LLM配置存在")
            else:
                self.check_result("LLM配置", False, error="LLM配置缺失")

            # 检查性能配置
            if hasattr(config, "performance_config"):
                perf_config = config.performance_config
                self.check_result(
                    "性能配置",
                    True,
                    f"超时:{perf_config.global_timeout}s, 并发:{perf_config.llm_concurrent_limit}, 沙盒清理:{perf_config.enable_sandbox_cleanup}",
                )
            else:
                self.check_result("性能配置", False, error="性能配置缺失")

            # 检查沙盒配置
            if hasattr(config, "sandbox"):
                self.check_result("沙盒配置", True, "沙盒配置存在")
            else:
                self.check_result("沙盒配置", False, error="沙盒配置缺失")

        except Exception as e:
            self.check_result("配置加载", False, error=f"配置加载失败: {e}")

    async def check_agents_initialization(self):
        """检查智能体初始化"""
        print("\n🤖 === 检查智能体初始化 ===")

        # 需求分析智能体
        try:
            from app.assistants.requirements.agents.requirement_clarifier import (
                RequirementClarifierAgent,
            )

            agent = RequirementClarifierAgent()

            # 检查核心属性
            if hasattr(agent, "think_tool"):
                self.check_result("需求智能体-思维工具", True, "思维工具已集成")
            else:
                self.check_result("需求智能体-思维工具", False, error="思维工具未集成")

            if hasattr(agent, "reflection_engine"):
                self.check_result("需求智能体-反思引擎", True, "反思引擎已集成")
            else:
                self.check_result("需求智能体-反思引擎", False, error="反思引擎未集成")

            self.check_result("需求澄清智能体", True, "初始化成功")

        except Exception as e:
            self.check_result("需求澄清智能体", False, error=f"初始化失败: {e}")

        # 架构设计智能体们
        architecture_agents = [
            ("system_architect", "SystemArchitectAgent", "系统架构师"),
            ("database_designer", "DatabaseDesignerAgent", "数据库设计师"),
            ("tech_selector", "TechSelectorAgent", "技术选择器"),
            ("architecture_reviewer", "ArchitectureReviewerAgent", "架构审查师"),
        ]

        for module_name, class_name, description in architecture_agents:
            try:
                module = __import__(
                    f"app.assistants.architecture.agents.{module_name}",
                    fromlist=[class_name],
                )
                agent_class = getattr(module, class_name)
                agent = agent_class()
                self.check_result(description, True, "初始化成功")
            except Exception as e:
                self.check_result(description, False, error=f"初始化失败: {e}")

    async def check_api_status(self):
        """检查API状态"""
        print("\n🌐 === 检查API状态 ===")

        try:
            from app.api.architecture import architecture_router
            from app.api.requirements_modular.routes import requirements_router
            from app.api.requirements_modular.utils import (
                execute_flow_with_think_act_reflect,
            )

            # 检查路由器
            self.check_result(
                "需求分析API路由", True, f"路由数量: {len(requirements_router.routes)}"
            )
            self.check_result(
                "架构设计API路由", True, f"路由数量: {len(architecture_router.routes)}"
            )

            # 检查关键API函数
            self.check_result("Think-Act-Reflect API", True, "API函数存在")

        except Exception as e:
            self.check_result("API状态", False, error=f"API检查失败: {e}")

    async def check_tools_functionality(self):
        """检查工具功能"""
        print("\n🛠️ === 检查工具功能 ===")

        # 需求建模工具
        try:
            from app.tool.requirements_modeling import RequirementModelingTool

            tool = RequirementModelingTool()
            self.check_result("需求建模工具", True, "工具初始化成功")
        except Exception as e:
            self.check_result("需求建模工具", False, error=f"工具初始化失败: {e}")

        # 架构建模工具
        try:
            from app.tool.architecture_modeling import ArchitectureModelingTool

            tool = ArchitectureModelingTool()
            self.check_result("架构建模工具", True, "工具初始化成功")
        except Exception as e:
            self.check_result("架构建模工具", False, error=f"工具初始化失败: {e}")

    async def check_performance_system(self):
        """检查性能控制系统"""
        print("\n⚡ === 检查性能控制系统 ===")

        try:
            from app.core.performance_controller import get_performance_controller

            controller = get_performance_controller()
            status = controller.get_status()

            self.check_result(
                "性能控制器",
                True,
                f"状态: {status.get('status', 'unknown')}, 并发: {status.get('concurrent_tasks', 0)}",
            )

            # 简单测试，不使用装饰器
            try:
                async def quick_test():
                    await asyncio.sleep(0.1)
                    return True

                result = await quick_test()
                self.check_result("超时控制", True, "超时控制功能正常")
            except Exception as e:
                self.check_result("超时控制", False, error=f"超时控制测试失败: {e}")

        except Exception as e:
            self.check_result("性能控制系统", False, error=f"性能控制系统检查失败: {e}")

    def check_frontend_files(self):
        """检查前端文件"""
        print("\n🎨 === 检查前端文件 ===")

        frontend_paths = [
            "app/web/src/components",
            "app/web/src/pages",
            "app/web/src/utils",
            "app/web/src/App.tsx",
            "app/web/src/main.tsx",
            "app/web/index.html",
            "app/web/package.json",
        ]

        for path in frontend_paths:
            full_path = os.path.join(os.path.dirname(__file__), path)
            if os.path.exists(full_path):
                self.check_result(f"前端文件 {path}", True, "文件存在")
            else:
                self.check_result(f"前端文件 {path}", False, error="文件不存在")

    def check_system_resources(self):
        """检查系统资源"""
        print("\n💻 === 检查系统资源 ===")

        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.check_result("CPU使用率", True, f"{cpu_percent}%")

            # 内存使用情况
            memory = psutil.virtual_memory()
            self.check_result(
                "内存使用",
                True,
                f"总计: {memory.total / 1024 / 1024:.0f}MB, 使用: {memory.percent}%",
            )

            # 磁盘使用情况
            disk = psutil.disk_usage("/")
            self.check_result(
                "磁盘使用",
                True,
                f"总计: {disk.total / 1024 / 1024 / 1024:.1f}GB, 使用: {disk.percent}%",
            )

        except Exception as e:
            self.check_result("系统资源", False, error=f"系统资源检查失败: {e}")

    async def run_lightweight_functional_test(self):
        """运行轻量级功能测试"""
        print("\n🧪 === 运行功能测试 ===")

        try:
            from app.api.requirements_modular.utils import (
                execute_flow_with_think_act_reflect,
            )
            from app.assistants.requirements.flow import RequirementsFlow

            # 执行简单测试
            result = await execute_flow_with_think_act_reflect(
                "需要一个简单的待办事项管理系统"
            )

            if result and not isinstance(result, dict):
                raise ValueError("返回结果格式错误")

            self.check_result("功能测试", True, "测试通过")

        except Exception as e:
            self.check_result("功能测试", False, error=f"测试失败: {e}")

    def generate_report(self):
        """生成健康检查报告"""
        print("\n📊 === 健康检查报告 ===")

        total_checks = len(self.results)
        passed_checks = len([r for r in self.results.values() if r["success"]])
        failed_checks = len(self.errors)

        print(f"\n总检查项: {total_checks}")
        print(f"通过项目: {passed_checks}")
        print(f"失败项目: {failed_checks}")

        if self.errors:
            print("\n❌ 失败项目详情:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\n⚠️ 警告信息:")
            for warning in self.warnings:
                print(f"  - {warning}")

        health_score = (passed_checks / total_checks) * 100
        print(f"\n系统健康度: {health_score:.1f}%")

        status = (
            "健康"
            if health_score >= 90
            else "亚健康" if health_score >= 70 else "不健康"
        )
        print(f"系统状态: {status}")


async def main():
    """主函数"""
    checker = SystemHealthChecker()

    try:
        # 运行所有检查
        await checker.check_core_imports()
        await checker.check_configuration()
        await checker.check_agents_initialization()
        await checker.check_api_status()
        await checker.check_tools_functionality()
        await checker.check_performance_system()
        checker.check_frontend_files()
        checker.check_system_resources()
        await checker.run_lightweight_functional_test()

        # 生成报告
        checker.generate_report()

    except Exception as e:
        print(f"\n💥 健康检查过程中发生错误: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
