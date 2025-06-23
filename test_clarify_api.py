#!/usr/bin/env python3
"""测试澄清API功能"""

import asyncio
import json
import time

import requests


def test_clarify_api():
    """测试澄清API的基本功能"""

    print("🧪 测试澄清API...")

    # 测试数据
    test_request = {
        "session_id": "test_session_123",
        "answer": "平台主要面向大学生和职场人士，需要支持视频直播、录播课程、在线作业、课程评价等功能。预计最大并发用户数在5000人左右。",
    }

    url = "http://localhost:8000/api/requirements/clarify"

    print(f"📝 测试会话ID: {test_request['session_id']}")
    print(f"📝 测试回答: {test_request['answer']}")
    print("⏱️ 开始请求...")

    start_time = time.time()

    try:
        response = requests.post(
            url,
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=120,  # 增加超时时间
        )

        elapsed_time = time.time() - start_time
        print(f"⏱️ 请求耗时: {elapsed_time:.2f}秒")
        print(f"📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            print("✅ 请求成功!")
            data = response.json()

            print("📋 返回数据结构:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            # 验证关键字段
            if "status" in data:
                print(f"🔍 澄清状态: {data['status']}")

            if "next_questions" in data:
                print(f"❓ 后续问题数量: {len(data.get('next_questions', []))}")

            if "progress" in data:
                progress = data.get("progress", {})
                print(f"📈 质量评分: {progress.get('overall_quality', 'N/A')}")
                print(f"🎯 目标导向评分: {progress.get('goal_oriented_score', 'N/A')}")

        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"📋 错误信息: {response.text}")

    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except requests.exceptions.RequestException as e:
        print(f"🚫 请求异常: {e}")
    except Exception as e:
        print(f"💥 未知错误: {e}")


if __name__ == "__main__":
    test_clarify_api()
