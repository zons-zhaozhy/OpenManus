#!/usr/bin/env python3
"""手动测试多轮澄清功能"""

import json
import time

import requests


def test_multi_round_clarification():
    """测试真实的多轮澄清流程"""

    base_url = "http://localhost:8000/api/requirements"
    session_id = f"test_session_{int(time.time())}"

    print(f"🚀 开始多轮澄清测试")
    print(f"📝 会话ID: {session_id}")
    print("=" * 80)

    # 第1轮：模糊需求
    print("第1轮：提交模糊需求")
    round1_data = {"session_id": session_id, "answer": "我想做一个电商平台"}

    response1 = make_clarification_request(base_url, round1_data)
    if response1:
        print_response_summary(response1, 1)

        if response1.get("status") == "continue_clarification":
            # 第2轮：回答部分问题
            print("\n" + "=" * 80)
            print("第2轮：回答部分澄清问题")
            round2_data = {
                "session_id": session_id,
                "answer": "主要卖数码产品，面向年轻消费者，预算100万，6个月完成开发",
            }

            response2 = make_clarification_request(base_url, round2_data)
            if response2:
                print_response_summary(response2, 2)

                if response2.get("status") == "continue_clarification":
                    # 第3轮：继续澄清
                    print("\n" + "=" * 80)
                    print("第3轮：提供更多细节")
                    round3_data = {
                        "session_id": session_id,
                        "answer": "需要支持移动端和Web端，用户注册登录，商品搜索，购物车，支付，订单管理等基础功能",
                    }

                    response3 = make_clarification_request(base_url, round3_data)
                    if response3:
                        print_response_summary(response3, 3)

                        if response3.get("status") == "continue_clarification":
                            # 第4轮：完善技术细节
                            print("\n" + "=" * 80)
                            print("第4轮：完善技术细节")
                            round4_data = {
                                "session_id": session_id,
                                "answer": "技术栈使用Java Spring Boot + React，数据库MySQL，预计日活用户1万，支付接入微信和支付宝",
                            }

                            response4 = make_clarification_request(
                                base_url, round4_data
                            )
                            if response4:
                                print_response_summary(response4, 4)


def make_clarification_request(base_url, data):
    """发送澄清请求"""
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/clarify",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            result["elapsed_time"] = elapsed_time
            return result
        else:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def print_response_summary(response, round_num):
    """打印响应摘要"""
    print(f"⏱️ 耗时: {response.get('elapsed_time', 0):.1f}秒")
    print(f"📊 状态: {response.get('status', 'unknown')}")

    progress = response.get("progress", {})
    if progress:
        print(f"📈 质量评分: {progress.get('overall_quality', 0):.2f}")
        print(f"🎯 目标导向评分: {progress.get('goal_oriented_score', 0):.2f}")
        print(
            f"🔄 当前轮次: {progress.get('round_count', 0)}/{progress.get('max_rounds', 5)}"
        )
        print(f"✅ 质量达标: {progress.get('quality_threshold_met', False)}")

    if response.get("status") == "continue_clarification":
        questions = response.get("next_questions", [])
        print(f"❓ 后续问题数: {len(questions)}")
        for i, q in enumerate(questions[:3], 1):  # 只显示前3个问题
            print(f"   {i}. {q}")
        if len(questions) > 3:
            print(f"   ... 还有 {len(questions) - 3} 个问题")
    elif response.get("status") == "clarification_complete":
        final_report = response.get("final_report", {})
        print(f"🎉 澄清完成!")
        print(f"📝 最终需求长度: {len(final_report.get('final_requirement', ''))}")
        print(f"🏁 完成原因: {progress.get('completion_reason', 'unknown')}")


if __name__ == "__main__":
    test_multi_round_clarification()
