#!/usr/bin/env python3
"""
测试SSE流式接口
"""

import json
import urllib.parse

import requests


def test_sse_stream():
    """测试SSE流式分析接口"""

    test_content = (
        "我想开发一个在线教育平台，支持视频课程、在线考试、学习进度跟踪等功能"
    )
    encoded_content = urllib.parse.quote(test_content)

    url = f"http://localhost:8000/api/requirements/analyze/stream?content={encoded_content}"

    print(f"🧪 测试SSE流式接口...")
    print(f"📝 测试需求: {test_content}")
    print(f"🔗 请求URL: {url}")
    print("=" * 50)

    try:
        headers = {"Accept": "text/event-stream", "Cache-Control": "no-cache"}

        response = requests.get(url, headers=headers, stream=True)

        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return

        print(f"✅ 连接成功，开始接收流式数据...")
        print("=" * 50)

        event_count = 0
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                event_count += 1
                data_str = line[6:]  # 去掉 'data: ' 前缀

                try:
                    data = json.loads(data_str)
                    event_type = data.get("type", "unknown")
                    message = data.get("message", "")
                    stage = data.get("stage", "")
                    progress = data.get("progress", "")

                    print(f"📦 事件 #{event_count}: {event_type}")
                    if stage:
                        print(f"   🎯 阶段: {stage}")
                    if message:
                        print(f"   💬 消息: {message}")
                    if progress:
                        print(f"   📊 进度: {progress}")
                    print()

                    # 如果是错误或完成事件，退出
                    if event_type in ["error", "complete"]:
                        break

                    # 限制接收事件数量，避免无限等待
                    if event_count >= 20:
                        print("⚠️ 已接收20个事件，停止测试")
                        break

                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"   原始数据: {data_str}")

        print("=" * 50)
        print(f"✅ 测试完成，共接收到 {event_count} 个事件")

    except Exception as e:
        print(f"💥 测试异常: {e}")


if __name__ == "__main__":
    test_sse_stream()
