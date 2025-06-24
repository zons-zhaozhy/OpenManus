#!/usr/bin/env python3
"""
OpenManus需求分析助手全面系统测试
测试范围：API接口、核心功能、改进验证、错误处理
"""

import asyncio
import json
import logging
import sys
import time
from typing import Any, Dict, List

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SystemTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.session_data = {}

    def log_test_result(
        self, test_name: str, success: bool, details: str = "", duration: float = 0
    ):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "duration": duration,
            "timestamp": time.time(),
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name} ({duration:.2f}s) - {details}")

    def test_backend_health(self) -> bool:
        """测试后端健康状态"""
        test_name = "后端健康检查"
        start_time = time.time()

        try:
            response = requests.get(f"{self.base_url}/health", timeout=15)
            duration = time.time() - start_time

            if response.status_code == 200:
                self.log_test_result(
                    test_name, True, f"状态码: {response.status_code}", duration
                )
                return True
            else:
                self.log_test_result(
                    test_name, False, f"状态码: {response.status_code}", duration
                )
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"连接失败: {str(e)}", duration)
            return False

    def test_api_docs(self) -> bool:
        """测试API文档访问"""
        test_name = "API文档访问"
        start_time = time.time()

        try:
            response = requests.get(f"{self.base_url}/docs", timeout=15)
            duration = time.time() - start_time

            if response.status_code == 200 and "swagger" in response.text.lower():
                self.log_test_result(test_name, True, "API文档正常加载", duration)
                return True
            else:
                self.log_test_result(
                    test_name, False, f"状态码: {response.status_code}", duration
                )
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"访问失败: {str(e)}", duration)
            return False

    def test_requirements_analysis(self) -> bool:
        """测试需求分析核心功能"""
        test_name = "需求分析核心功能"
        start_time = time.time()

        try:
            # 测试需求分析接口
            test_requirement = (
                "我想开发一个在线教育平台，支持视频课程、在线考试、学习进度跟踪等功能"
            )

            payload = {"content": test_requirement, "project_context": "在线教育项目"}

            response = requests.post(
                f"{self.base_url}/api/requirements/analyze", json=payload, timeout=120
            )

            duration = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # 检查返回数据结构
                has_questions = "clarification_questions" in str(result)
                has_analysis = "initial_analysis" in str(result) or "result" in result

                if has_questions and has_analysis:
                    # 保存会话数据用于后续测试
                    self.session_data["analyze_result"] = result
                    self.log_test_result(
                        test_name, True, f"分析成功，包含澄清问题和初始分析", duration
                    )
                    return True
                else:
                    self.log_test_result(
                        test_name,
                        False,
                        f"返回数据结构不完整: {list(result.keys()) if result else 'None'}",
                        duration,
                    )
                    return False
            else:
                self.log_test_result(
                    test_name,
                    False,
                    f"状态码: {response.status_code}, 响应: {response.text[:200]}",
                    duration,
                )
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"请求失败: {str(e)}", duration)
            return False

    def test_goal_oriented_scoring(self) -> bool:
        """测试目标导向评分机制（我们的重要改进）"""
        test_name = "目标导向评分机制"
        start_time = time.time()

        try:
            if not self.session_data.get("analyze_result"):
                self.log_test_result(test_name, False, "缺少前置分析结果", 0)
                return False

            # 模拟澄清回答
            clarification_payload = {
                "session_id": "test_session_123",
                "answer": "这是一个面向K12学生的在线教育平台，需要支持多媒体课程内容，包括视频、音频、PPT等。用户主要是学生、老师和家长三个角色。",
                "question": "请详细说明目标用户群体和核心功能需求",
            }

            response = requests.post(
                f"{self.base_url}/api/requirements/clarify",
                json=clarification_payload,
                timeout=120,
            )

            duration = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # 检查是否包含目标导向评分
                has_goal_score = "goal_oriented_score" in str(result)
                has_quality_score = "overall_quality" in str(
                    result
                ) or "quality" in str(result)

                if has_goal_score:
                    self.log_test_result(
                        test_name, True, "目标导向评分机制正常工作", duration
                    )
                    return True
                else:
                    self.log_test_result(
                        test_name,
                        False,
                        f"未发现目标导向评分，返回: {list(result.keys()) if result else 'None'}",
                        duration,
                    )
                    return False
            else:
                self.log_test_result(
                    test_name,
                    False,
                    f"状态码: {response.status_code}, 响应: {response.text[:200]}",
                    duration,
                )
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"测试失败: {str(e)}", duration)
            return False

    def test_learning_system(self) -> bool:
        """测试自适应学习系统"""
        test_name = "自适应学习系统"
        start_time = time.time()

        try:
            response = requests.get(
                f"{self.base_url}/api/requirements/learning_statistics", timeout=10
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                if "statistics" in result or "status" in result:
                    self.log_test_result(test_name, True, "学习统计接口正常", duration)
                    return True
                else:
                    self.log_test_result(
                        test_name, False, f"返回数据异常: {result}", duration
                    )
                    return False
            else:
                self.log_test_result(
                    test_name, False, f"状态码: {response.status_code}", duration
                )
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"请求失败: {str(e)}", duration)
            return False

    def test_frontend_accessibility(self) -> bool:
        """测试前端页面可访问性"""
        test_name = "前端页面访问"
        start_time = time.time()

        try:
            response = requests.get("http://localhost:5173", timeout=10)
            duration = time.time() - start_time

            if response.status_code == 200:
                # 检查是否包含核心前端元素
                html_content = response.text.lower()
                has_react = "react" in html_content or "vite" in html_content
                has_title = "openmanus" in html_content or "需求分析" in html_content

                if has_react or has_title:
                    self.log_test_result(test_name, True, "前端页面正常加载", duration)
                    return True
                else:
                    self.log_test_result(test_name, False, "前端内容异常", duration)
                    return False
            else:
                self.log_test_result(
                    test_name, False, f"状态码: {response.status_code}", duration
                )
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"连接失败: {str(e)}", duration)
            return False

    def test_error_handling(self) -> bool:
        """测试错误处理机制"""
        test_name = "错误处理机制"
        start_time = time.time()

        try:
            # 测试无效请求
            invalid_payload = {"invalid": "data"}

            response = requests.post(
                f"{self.base_url}/api/requirements/analyze",
                json=invalid_payload,
                timeout=10,
            )

            duration = time.time() - start_time

            # 应该返回错误但不崩溃
            if response.status_code in [400, 422, 500]:
                self.log_test_result(
                    test_name,
                    True,
                    f"正确处理无效请求，状态码: {response.status_code}",
                    duration,
                )
                return True
            else:
                self.log_test_result(
                    test_name,
                    False,
                    f"错误处理异常，状态码: {response.status_code}",
                    duration,
                )
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"测试失败: {str(e)}", duration)
            return False

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行全面测试"""
        logger.info("🚀 开始 OpenManus 全面系统测试...")

        test_suite = [
            (
                "基础连接测试",
                [
                    self.test_backend_health,
                    self.test_api_docs,
                    self.test_frontend_accessibility,
                ],
            ),
            (
                "核心功能测试",
                [
                    self.test_requirements_analysis,
                    self.test_goal_oriented_scoring,
                    self.test_learning_system,
                ],
            ),
            ("稳定性测试", [self.test_error_handling]),
        ]

        total_tests = 0
        passed_tests = 0

        for suite_name, tests in test_suite:
            logger.info(f"\n📋 执行测试组: {suite_name}")

            for test_func in tests:
                total_tests += 1
                if test_func():
                    passed_tests += 1

        # 生成测试报告
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        report = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "detailed_results": self.test_results,
            "test_summary": self.generate_test_summary(),
            "recommendations": self.generate_recommendations(),
        }

        self.print_final_report(report)
        return report

    def generate_test_summary(self) -> str:
        """生成测试摘要"""
        passed = len([r for r in self.test_results if r["success"]])
        failed = len([r for r in self.test_results if not r["success"]])

        if failed == 0:
            return f"🎉 所有测试通过！系统运行状态：优秀"
        elif failed <= 2:
            return f"⚠️ 大部分测试通过，存在 {failed} 个问题需要关注"
        else:
            return f"❌ 系统存在 {failed} 个严重问题，需要立即修复"

    def generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        failed_tests = [r for r in self.test_results if not r["success"]]

        for test in failed_tests:
            if "健康检查" in test["test_name"]:
                recommendations.append("🔧 检查后端服务配置和端口绑定")
            elif "前端" in test["test_name"]:
                recommendations.append("🎨 检查前端构建和开发服务器状态")
            elif "目标导向" in test["test_name"]:
                recommendations.append("⚡ 验证目标导向评分机制的集成")
            elif "学习系统" in test["test_name"]:
                recommendations.append("🧠 检查自适应学习系统的配置")
            elif "需求分析" in test["test_name"]:
                recommendations.append("📝 验证需求分析API的数据结构")

        if not recommendations:
            recommendations.append("✨ 系统运行良好，建议定期进行性能优化和功能增强")

        return recommendations

    def print_final_report(self, report: Dict[str, Any]):
        """打印最终测试报告"""
        print("\n" + "=" * 80)
        print("🎯 OpenManus 需求分析助手 - 全面测试报告")
        print("=" * 80)

        print(f"\n📊 测试统计:")
        print(f"   总测试数: {report['total_tests']}")
        print(f"   通过测试: {report['passed_tests']}")
        print(f"   失败测试: {report['failed_tests']}")
        print(f"   成功率: {report['success_rate']:.1f}%")

        print(f"\n📋 测试摘要:")
        print(f"   {report['test_summary']}")

        print(f"\n💡 改进建议:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"   {i}. {rec}")

        print(f"\n🔍 详细结果:")
        for result in report["detailed_results"]:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test_name']}: {result['details']}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        tester = SystemTester()
        report = tester.run_comprehensive_test()

        # 保存测试报告
        with open("comprehensive_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细测试报告已保存到: comprehensive_test_report.json")

        # 根据测试结果返回合适的退出码
        exit_code = 0 if report["success_rate"] >= 80 else 1
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试执行异常: {e}")
        sys.exit(1)
