#!/usr/bin/env python3
"""
SSE流式接口完整测试
"""

import json
import urllib.parse

import requests


def test_sse_stream():
    """测试SSE流式接口"""

    print("🧪 测试SSE流式需求分析接口...")

    test_content = (
        "我想开发一个在线教育平台，支持视频课程、在线考试、学习进度跟踪等功能"
    )
    encoded_content = urllib.parse.quote(test_content)
    url = f"http://localhost:8000/api/requirements/analyze/stream?content={encoded_content}"

    print(f"📝 测试需求: {test_content}")
    print(f"🔗 请求URL: {url}")
    print("=" * 60)

    try:
        headers = {"Accept": "text/event-stream", "Cache-Control": "no-cache"}

        response = requests.get(url, headers=headers, stream=True, timeout=60)

        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

        print(f"✅ 连接成功，开始接收流式数据...")
        print("=" * 60)

        events_received = 0
        stages_seen = set()
        has_result = False
        has_complete = False

        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                events_received += 1
                data_str = line[6:]  # 去掉 'data: ' 前缀

                try:
                    data = json.loads(data_str)
                    event_type = data.get("type", "unknown")
                    message = data.get("message", "")
                    stage = data.get("stage", "")
                    progress = data.get("progress", "")

                    print(f"📦 事件 #{events_received}: {event_type}")
                    if stage:
                        print(f"   🎯 阶段: {stage}")
                        stages_seen.add(stage)
                    if message:
                        print(f"   💬 消息: {message}")
                    if progress:
                        print(f"   📊 进度: {progress}")
                    print()

                    # 记录重要事件
                    if event_type == "result":
                        has_result = True
                    if event_type == "complete":
                        has_complete = True

                    # 如果是错误或完成事件，退出
                    if event_type in ["error", "complete"]:
                        break

                    # 限制接收事件数量，避免无限等待
                    if events_received >= 25:
                        print("⚠️ 已接收25个事件，停止测试")
                        break

                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"   原始数据: {data_str}")

        print("=" * 60)
        print(f"✅ 测试完成！")
        print(f"📊 统计信息:")
        print(f"   - 接收事件数: {events_received}")
        print(f"   - 经历阶段数: {len(stages_seen)}")
        print(f"   - 阶段列表: {', '.join(stages_seen)}")
        print(f"   - 有结果事件: {has_result}")
        print(f"   - 有完成事件: {has_complete}")

        # 判断测试是否成功
        success = (
            events_received >= 5  # 至少收到5个事件
            and len(stages_seen) >= 3  # 至少经历3个阶段
            and has_complete  # 有完成事件
        )

        if success:
            print("🎉 SSE流式测试全面通过！")
        else:
            print("⚠️ SSE流式测试部分通过，但可能有改进空间")

        return success

    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"💥 测试异常: {e}")
        return False


def test_regular_api():
    """测试常规POST API"""
    print("🧪 测试常规POST需求分析接口...")

    url = "http://localhost:8000/api/requirements/analyze"
    test_data = {
        "content": "我想开发一个简单的待办事项应用",
        "project_context": "个人项目",
    }

    try:
        response = requests.post(url, json=test_data, timeout=120)

        if response.status_code == 200:
            result = response.json()
            print("✅ 常规API测试成功")
            print(f"📄 返回会话ID: {result.get('session_id', 'N/A')}")
            print(f"📄 处理时间: {result.get('processing_time', 'N/A')}秒")
            return True
        else:
            print(f"❌ 常规API测试失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 常规API测试异常: {e}")
        return False


if __name__ == "__main__":
    print("🏁 开始OpenManus需求分析API测试...")
    print("=" * 60)

    # 测试常规API
    regular_result = test_regular_api()
    print()

    # 测试SSE流式API
    sse_result = test_sse_stream()

    print("=" * 60)
    print("📋 测试总结:")
    print(f"   常规POST API: {'✅ 通过' if regular_result else '❌ 失败'}")
    print(f"   SSE流式API: {'✅ 通过' if sse_result else '❌ 失败'}")

    if regular_result and sse_result:
        print("🎊 所有API测试通过！OpenManus需求分析功能运行正常！")
    else:
        print("⚠️ 部分API测试失败，需要检查服务状态")
