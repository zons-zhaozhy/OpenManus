#!/usr/bin/env python3
"""
单独测试需求分析API
"""

import json
import time

import requests


def test_requirements_api():
    """测试需求分析API"""
    url = "http://localhost:8000/api/requirements/analyze"

    test_requirement = (
        "我想开发一个在线教育平台，支持视频课程、在线考试、学习进度跟踪等功能"
    )

    payload = {"content": test_requirement, "project_context": "在线教育项目"}

    print(f"🧪 测试需求分析API...")
    print(f"📝 测试需求: {test_requirement}")
    print(f"⏱️ 开始请求...")

    start_time = time.time()

    try:
        response = requests.post(url, json=payload, timeout=60)
        duration = time.time() - start_time

        print(f"⏱️ 请求耗时: {duration:.2f}秒")
        print(f"📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功!")
            print(f"📋 返回数据结构:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 请求失败!")
            print(f"📄 错误响应: {response.text}")

    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 请求异常: {e}")
        print(f"⏱️ 异常耗时: {duration:.2f}秒")


if __name__ == "__main__":
    test_requirements_api()
