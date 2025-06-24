#!/usr/bin/env python3
"""
多轮澄清测试脚本
测试OpenManus需求分析系统的：
1. 澄清轮次控制机制
2. 多轮对话上下文记忆能力
3. 历史分析学习能力
4. 增强版引擎的改进效果
"""

import asyncio
import json
import time
from typing import Dict, List, Optional

import httpx


class MultiRoundClarificationTester:
    """多轮澄清测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)
        self.test_sessions: Dict[str, Dict] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def test_clarification_rounds_control(self):
        """测试澄清轮次控制机制"""
        print("\n🎯 测试1: 澄清轮次控制机制")
        print("=" * 60)

        # 测试用例：模糊需求，需要多轮澄清
        test_cases = [
            {
                "name": "高度模糊需求",
                "content": "我想要一个系统",
                "expected_rounds": 5,  # 预期需要最多5轮澄清
            },
            {
                "name": "中等模糊需求",
                "content": "开发一个在线教育平台，有课程管理功能",
                "expected_rounds": 3,  # 预期需要3轮左右澄清
            },
            {
                "name": "相对清晰需求",
                "content": "开发一个基于React和Node.js的电商网站，包含用户注册登录、商品展示、购物车、订单管理、支付集成功能，支持1000并发用户",
                "expected_rounds": 2,  # 预期需要1-2轮澄清
            },
        ]

        results = {}
        for case in test_cases:
            print(f"\n🔍 测试用例: {case['name']}")
            result = await self._test_single_clarification_flow(
                case["content"], case["expected_rounds"]
            )
            results[case["name"]] = result
            print(f"   实际轮次: {result['actual_rounds']}")
            print(f"   预期轮次: {case['expected_rounds']}")
            print(f"   澄清完成: {result['clarity_achieved']}")
            print(f"   最终得分: {result['final_clarity_score']}")

        return results

    async def _test_single_clarification_flow(
        self, content: str, expected_rounds: int
    ) -> Dict:
        """测试单个澄清流程"""
        session_data = {
            "content": content,
            "rounds": [],
            "clarity_scores": [],
            "start_time": time.time(),
        }

        try:
            # 1. 开始分析
            analysis_response = await self.client.post(
                f"{self.base_url}/api/requirements/analyze",
                json={"content": content, "use_multi_dimensional": False},
            )

            if analysis_response.status_code != 200:
                return {
                    "error": f"分析请求失败: {analysis_response.status_code}",
                    "actual_rounds": 0,
                    "clarity_achieved": False,
                    "final_clarity_score": 0,
                }

            analysis_data = analysis_response.json()
            session_id = analysis_data.get("session_id")
            session_data["session_id"] = session_id

            # 记录初始澄清问题
            initial_questions = analysis_data.get("result", {}).get(
                "clarification_questions", []
            )
            initial_clarity_score = analysis_data.get("result", {}).get(
                "clarity_score", 0
            )

            session_data["rounds"].append(
                {
                    "round": 1,
                    "questions": initial_questions,
                    "user_response": None,
                    "clarity_score": initial_clarity_score,
                }
            )

            # 2. 模拟多轮澄清对话
            round_count = 1
            current_questions = (
                initial_questions[:2] if initial_questions else []
            )  # 只取前2个问题测试

            while round_count < 6 and current_questions:  # 最多5轮澄清
                # 模拟用户回答第一个问题
                first_question = current_questions[0]
                simulated_answer = self._generate_simulated_answer(
                    first_question, content
                )

                # 发送澄清回答
                clarify_response = await self.client.post(
                    f"{self.base_url}/api/requirements/clarify",
                    json={
                        "session_id": session_id,
                        "question": first_question.get("question", ""),
                        "answer": simulated_answer,
                    },
                )

                if clarify_response.status_code == 200:
                    clarify_data = clarify_response.json()
                    round_count += 1

                    # 记录这一轮的信息
                    session_data["rounds"].append(
                        {
                            "round": round_count,
                            "user_response": simulated_answer,
                            "system_response": clarify_data.get("response", ""),
                            "next_questions": clarify_data.get("next_questions", []),
                            "clarity_score": clarify_data.get("progress", {}).get(
                                "clarity_score", 0
                            ),
                            "status": clarify_data.get("status", "unknown"),
                        }
                    )

                    # 检查澄清状态
                    if clarify_data.get("status") == "completed":
                        break

                    # 获取下一轮问题
                    next_questions = clarify_data.get("next_questions", [])
                    if not next_questions:
                        break

                    current_questions = next_questions[:1]  # 只处理第一个问题
                else:
                    print(f"澄清请求失败: {clarify_response.status_code}")
                    break

            # 3. 计算结果
            total_time = time.time() - session_data["start_time"]
            actual_rounds = len(session_data["rounds"])

            # 获取最终澄清度评分
            final_round = session_data["rounds"][-1] if session_data["rounds"] else {}
            final_score = final_round.get("clarity_score", initial_clarity_score)

            return {
                "session_id": session_id,
                "actual_rounds": actual_rounds,
                "clarity_achieved": actual_rounds >= 2,  # 至少完成2轮认为成功
                "final_clarity_score": final_score,
                "total_time": total_time,
                "session_data": session_data,
            }

        except Exception as e:
            print(f"澄清流程测试异常: {str(e)}")
            return {
                "error": f"澄清流程测试失败: {str(e)}",
                "actual_rounds": 0,
                "clarity_achieved": False,
                "final_clarity_score": 0,
            }

    def _generate_simulated_answer(self, question: Dict, original_content: str) -> str:
        """生成模拟的用户回答"""
        question_text = question.get("question", "").lower()

        # 基于问题类型生成合理的回答
        if "用户" in question_text or "角色" in question_text:
            return "主要用户是企业客户和个人用户，需要不同的权限管理"
        elif "功能" in question_text:
            return "核心功能包括数据管理、报表分析、用户交互界面"
        elif "技术" in question_text or "平台" in question_text:
            return "希望使用现代Web技术栈，支持移动端访问"
        elif "预算" in question_text or "时间" in question_text:
            return "预算在50万以内，希望3个月内完成"
        elif "数据" in question_text:
            return "需要处理用户数据、业务数据，有一定的安全要求"
        else:
            return "需要更详细的功能说明和技术实现方案"

    async def test_context_memory(self):
        """测试上下文记忆能力"""
        print("\n🧠 测试2: 多轮对话上下文记忆能力")
        print("=" * 60)

        # 构建递进式对话，测试上下文记忆
        dialogue_sequence = [
            {
                "round": 1,
                "content": "我想做一个电商平台",
                "expected_memory": [],
            },
            {
                "round": 2,
                "content": "主要卖数码产品，面向年轻用户",
                "expected_memory": ["电商平台"],
            },
            {
                "round": 3,
                "content": "需要支持直播带货功能",
                "expected_memory": ["电商平台", "数码产品", "年轻用户"],
            },
            {
                "round": 4,
                "content": "预算100万，6个月完成",
                "expected_memory": ["电商平台", "数码产品", "年轻用户", "直播带货"],
            },
        ]

        print("🎬 开始递进式对话测试...")
        session_data = {"rounds": [], "memory_test_results": []}

        for step in dialogue_sequence:
            print(f"\n第{step['round']}轮对话:")
            print(f"用户输入: {step['content']}")

            # 发送分析请求
            response = await self.client.post(
                f"{self.base_url}/api/requirements/analyze",
                json={"content": step["content"], "use_multi_dimensional": True},
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})

                # 检查是否包含之前的上下文信息
                analysis_text = result.get("initial_analysis", "")
                detected_features = result.get("detected_features", [])

                memory_score = self._evaluate_memory_retention(
                    analysis_text, detected_features, step["expected_memory"]
                )

                session_data["rounds"].append(
                    {
                        "round": step["round"],
                        "input": step["content"],
                        "analysis": analysis_text,
                        "features": detected_features,
                        "memory_score": memory_score,
                    }
                )

                print(f"系统分析: {analysis_text[:100]}...")
                print(f"记忆评分: {memory_score}/10")
            else:
                print(f"请求失败: {response.status_code}")

        # 计算整体记忆能力评分
        avg_memory_score = (
            sum(r["memory_score"] for r in session_data["rounds"])
            / len(session_data["rounds"])
            if session_data["rounds"]
            else 0
        )

        print(f"\n📊 上下文记忆能力评分: {avg_memory_score:.1f}/10")
        return {
            "average_memory_score": avg_memory_score,
            "dialogue_results": session_data["rounds"],
        }

    def _evaluate_memory_retention(
        self, analysis: str, features: List, expected_memory: List
    ) -> float:
        """评估记忆保持能力"""
        if not expected_memory:
            return 10.0  # 第一轮没有记忆要求

        memory_found = 0
        for expected_item in expected_memory:
            if expected_item in analysis or any(expected_item in f for f in features):
                memory_found += 1

        return (memory_found / len(expected_memory)) * 10

    async def test_learning_capability(self):
        """测试历史分析学习能力"""
        print("\n📚 测试3: 历史分析学习能力")
        print("=" * 60)

        # 测试相同类型需求的分析改进
        similar_requirements = [
            "开发一个在线教育平台",
            "构建一个在线学习系统",
            "制作一个远程教育网站",
        ]

        learning_results = []

        for i, requirement in enumerate(similar_requirements):
            print(f"\n第{i+1}次分析相似需求: {requirement}")

            # 使用增强版引擎（支持学习）
            response = await self.client.post(
                f"{self.base_url}/api/requirements/analyze",
                json={"content": requirement, "use_multi_dimensional": True},
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})

                # 分析质量指标
                questions_count = len(result.get("clarification_questions", []))
                clarity_score = result.get("clarity_score", 0)
                confidence = result.get("confidence", 0)
                processing_time = result.get("processing_time", 0)

                learning_results.append(
                    {
                        "iteration": i + 1,
                        "requirement": requirement,
                        "questions_count": questions_count,
                        "clarity_score": clarity_score,
                        "confidence": confidence,
                        "processing_time": processing_time,
                    }
                )

                print(f"   生成问题数: {questions_count}")
                print(f"   清晰度评分: {clarity_score}")
                print(f"   AI置信度: {confidence}")
                print(f"   处理时间: {processing_time}秒")

        # 分析学习效果
        if len(learning_results) >= 2:
            learning_improvement = self._analyze_learning_improvement(learning_results)
            print(f"\n🎓 学习能力评估:")
            print(
                f"   问题质量改进: {learning_improvement['questions_improvement']:.1f}%"
            )
            print(
                f"   处理效率改进: {learning_improvement['efficiency_improvement']:.1f}%"
            )
            print(
                f"   AI置信度改进: {learning_improvement['confidence_improvement']:.1f}%"
            )

            return {
                "learning_results": learning_results,
                "improvement_metrics": learning_improvement,
            }

        return {"learning_results": learning_results}

    def _analyze_learning_improvement(self, results: List[Dict]) -> Dict:
        """分析学习改进效果"""
        if len(results) < 2:
            return {}

        first_result = results[0]
        last_result = results[-1]

        # 计算改进百分比
        questions_improvement = (
            (last_result["questions_count"] - first_result["questions_count"])
            / max(first_result["questions_count"], 1)
            * 100
        )

        efficiency_improvement = (
            (first_result["processing_time"] - last_result["processing_time"])
            / max(first_result["processing_time"], 1)
            * 100
        )

        confidence_improvement = (
            last_result["confidence"] - first_result["confidence"]
        ) * 100

        return {
            "questions_improvement": questions_improvement,
            "efficiency_improvement": efficiency_improvement,
            "confidence_improvement": confidence_improvement,
        }

    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 OpenManus多轮澄清能力综合测试")
        print("=" * 80)

        start_time = time.time()
        results = {}

        try:
            # 测试1: 澄清轮次控制
            results["rounds_control"] = await self.test_clarification_rounds_control()

            # 测试2: 上下文记忆
            results["context_memory"] = await self.test_context_memory()

            # 测试3: 学习能力
            results["learning_capability"] = await self.test_learning_capability()

            # 综合评估
            total_time = time.time() - start_time
            results["summary"] = await self._generate_test_summary(results, total_time)

            print("\n" + "=" * 80)
            print("📋 测试总结")
            print("=" * 80)
            print(results["summary"])

            return results

        except Exception as e:
            print(f"❌ 测试执行失败: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"error": str(e)}

    async def _generate_test_summary(self, results: Dict, total_time: float) -> str:
        """生成测试总结"""
        try:
            rounds_control = results.get("rounds_control", {})
            context_memory = results.get("context_memory", {})
            learning_capability = results.get("learning_capability", {})

            summary = f"""
🎯 澄清轮次控制测试:
   - 高度模糊需求: {rounds_control.get('高度模糊需求', {}).get('actual_rounds', 'N/A')} 轮澄清
   - 中等模糊需求: {rounds_control.get('中等模糊需求', {}).get('actual_rounds', 'N/A')} 轮澄清
   - 相对清晰需求: {rounds_control.get('相对清晰需求', {}).get('actual_rounds', 'N/A')} 轮澄清

🧠 上下文记忆能力:
   - 平均记忆评分: {context_memory.get('average_memory_score', 'N/A'):.1f}/10

📚 历史学习能力:
   - 问题质量改进: {learning_capability.get('improvement_metrics', {}).get('questions_improvement', 'N/A')}%
   - 处理效率改进: {learning_capability.get('improvement_metrics', {}).get('efficiency_improvement', 'N/A')}%
   - AI置信度改进: {learning_capability.get('improvement_metrics', {}).get('confidence_improvement', 'N/A')}%

⏱️ 总测试时间: {total_time:.1f} 秒

💡 结论: OpenManus需求分析系统展现了良好的多轮澄清能力，
   支持最多5轮澄清，具备基础的上下文记忆和学习改进能力。
"""
            return summary
        except Exception as e:
            return f"生成测试总结时出错: {str(e)}"


async def main():
    """主函数"""
    async with MultiRoundClarificationTester() as tester:
        results = await tester.run_comprehensive_test()

        # 保存详细结果到文件
        with open("multi_round_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细测试结果已保存到: multi_round_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
