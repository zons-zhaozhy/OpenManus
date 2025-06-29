#!/usr/bin/env python3
"""
弹性超时功能测试脚本

测试新的智能超时控制系统，验证：
1. 基础超时后如果有响应能继续执行
2. 长时间无响应会被正确终止
3. 绝对最大超时限制生效
"""

import asyncio
import json
import time

import requests


async def test_elastic_timeout_api():
    """测试API的弹性超时功能"""

    print("🧪 弹性超时功能测试")
    print("=" * 60)

    # 测试数据
    test_request = {
        "content": "我想开发一个具有实时聊天功能的社交电商平台，需要支持用户注册登录、商品浏览购买、在线支付、订单管理、客服系统等功能",
        "use_multi_dimensional": True,
        "enable_conflict_detection": True,
    }

    print("📝 测试需求：", test_request["content"][:50] + "...")
    print("⏱️  开始测试弹性超时...")

    start_time = time.time()

    try:
        # 发送需求分析请求
        response = requests.post(
            "http://localhost:8000/api/requirements/analyze",
            json=test_request,
            timeout=300,  # 客户端超时设为5分钟
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功完成!")
            print(f"⏱️  总耗时: {elapsed:.2f}s")

            # 检查返回结果
            if "session_id" in result:
                print(f"📋 会话ID: {result['session_id']}")

            if "processing_metrics" in result:
                metrics = result["processing_metrics"]
                print(f"📊 处理指标:")
                print(f"   - 处理时间: {metrics.get('processing_time', 0):.2f}s")
                print(f"   - 版本: {metrics.get('analysis_version', 'unknown')}")
                print(f"   - 学习成熟度: {metrics.get('learning_maturity', 0):.2f}")

            if "learning_insights" in result and result["learning_insights"]:
                print(f"🎯 学习洞察: {len(result['learning_insights'])}条")

        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"⏱️  失败耗时: {elapsed:.2f}s")
            print(f"📄 错误信息: {response.text}")

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"⏰ 客户端超时: {elapsed:.2f}s")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"💥 异常错误: {e}")
        print(f"⏱️  错误耗时: {elapsed:.2f}s")


async def test_concurrent_requests():
    """测试并发请求下的弹性超时"""

    print("\n🚀 并发弹性超时测试")
    print("=" * 60)

    async def send_request(req_id: int):
        """发送单个异步请求"""
        start_time = time.time()
        print(f"🔹 请求{req_id} 开始...")

        try:
            # 模拟异步HTTP请求（这里用同步requests，实际可用aiohttp）
            import aiohttp

            async with aiohttp.ClientSession() as session:
                test_data = {
                    "content": f"请求{req_id}：开发一个AI驱动的智能推荐系统，包含用户画像分析、商品推荐算法、A/B测试框架等",
                    "use_multi_dimensional": True,
                    "enable_conflict_detection": True,
                }

                async with session.post(
                    "http://localhost:8000/api/requirements/analyze",
                    json=test_data,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as response:
                    elapsed = time.time() - start_time

                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 请求{req_id} 成功: {elapsed:.2f}s")
                        return f"请求{req_id}成功"
                    else:
                        text = await response.text()
                        print(
                            f"❌ 请求{req_id} 失败({response.status}): {elapsed:.2f}s"
                        )
                        return f"请求{req_id}失败"

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"💥 请求{req_id} 异常: {e} ({elapsed:.2f}s)")
            return f"请求{req_id}异常"

    # 并发发送3个请求
    tasks = [send_request(i) for i in range(1, 4)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    print(f"\n📊 并发测试结果:")
    for i, result in enumerate(results, 1):
        print(f"   - {result}")


async def check_system_status():
    """检查系统状态"""

    print("\n🔍 系统状态检查")
    print("=" * 60)

    try:
        # 检查健康状态
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ 后端服务正常")
        else:
            print(f"⚠️  后端服务异常: {response.status_code}")

        # 检查学习统计
        response = requests.get(
            "http://localhost:8000/api/requirements/learning_statistics", timeout=10
        )
        if response.status_code == 200:
            stats = response.json()
            if "statistics" in stats:
                s = stats["statistics"]
                print(f"📈 学习统计:")
                print(f"   - 总案例数: {s.get('total_cases', 0)}")
                print(f"   - 学习成熟度: {s.get('learning_maturity', 0):.2f}")
                print(f"   - 洞察总数: {s.get('total_insights', 0)}")

    except Exception as e:
        print(f"❌ 状态检查失败: {e}")


async def main():
    """主测试函数"""

    print("🧪 OpenManus 弹性超时系统测试")
    print("🕐 开始时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    # 检查系统状态
    await check_system_status()

    # 测试单个请求的弹性超时
    await test_elastic_timeout_api()

    # 测试并发请求
    try:
        await test_concurrent_requests()
    except Exception as e:
        print(f"⚠️  并发测试跳过: {e}")

    print("\n" + "=" * 60)
    print("🏁 测试完成:", time.strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    asyncio.run(main())
