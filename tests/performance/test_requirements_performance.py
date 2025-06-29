"""
需求分析模块的性能测试
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import pytest

from app.api.requirements_modular.handlers import (
    AnalysisHandler,
    ClarificationHandler,
    SessionHandler,
    WorkflowHandler,
)
from app.api.requirements_modular.utils import (
    active_sessions,
    execute_flow_with_think_act_reflect,
    session_storage,
)
from app.core.adaptive_learning_system import AnalysisCase
from app.logger import logger


class TestRequirementsPerformance:
    """需求分析模块性能测试"""

    @pytest.mark.asyncio
    async def test_analysis_performance(self):
        """测试需求分析性能"""
        test_cases = [
            ("需要开发一个在线商城系统", "small"),
            (
                "需要开发一个在线商城系统，包含用户管理、商品管理、订单管理、支付管理等功能",
                "medium",
            ),
            (
                "需要开发一个在线商城系统，包含以下功能：\n"
                "1. 用户管理：注册、登录、个人信息管理\n"
                "2. 商品管理：商品分类、商品上架、商品搜索\n"
                "3. 订单管理：购物车、下单、订单跟踪\n"
                "4. 支付管理：在线支付、退款处理\n"
                "5. 物流管理：发货、物流跟踪\n"
                "6. 评价管理：商品评价、评价回复\n"
                "7. 促销管理：优惠券、限时特价\n"
                "8. 统计分析：销售统计、用户分析\n",
                "large",
            ),
        ]

        results = []
        for content, size in test_cases:
            start_time = time.time()
            result = await AnalysisHandler.analyze_requirement({"content": content})
            end_time = time.time()

            processing_time = end_time - start_time
            results.append((size, processing_time, result.get("session_id")))

        # 输出性能报告
        print("\n需求分析性能测试结果:")
        print("=" * 50)
        for size, processing_time, session_id in results:
            print(f"需求规模: {size}")
            print(f"处理时间: {processing_time:.2f}秒")
            print(f"会话ID: {session_id}")
            print("-" * 30)

        # 验证性能指标
        for size, processing_time, _ in results:
            if size == "small":
                assert processing_time < 5.0, "小规模需求分析超时"
            elif size == "medium":
                assert processing_time < 10.0, "中等规模需求分析超时"
            else:
                assert processing_time < 20.0, "大规模需求分析超时"

        return results

    @pytest.mark.asyncio
    async def test_clarification_performance(self):
        """测试需求澄清性能"""
        # 首先创建一个测试会话
        content = "需要开发一个在线商城系统"
        result = await AnalysisHandler.analyze_requirement({"content": content})
        session_id = result["session_id"]

        test_answers = [
            "系统需要支持100个并发用户",
            "需要使用React和Node.js技术栈",
            "预算在50万以内，开发周期3个月",
            "需要支持微信和支付宝支付",
            "系统需要部署在阿里云上",
        ]

        results = []
        for answer in test_answers:
            start_time = time.time()
            result = await ClarificationHandler.process_clarification(
                session_id=session_id,
                answer=answer,
            )
            end_time = time.time()

            processing_time = end_time - start_time
            results.append((answer, processing_time))

        # 输出性能报告
        print("\n需求澄清性能测试结果:")
        print("=" * 50)
        for answer, processing_time in results:
            print(f"回答内容: {answer[:30]}...")
            print(f"处理时间: {processing_time:.2f}秒")
            print("-" * 30)

        # 验证性能指标
        for _, processing_time in results:
            assert processing_time < 3.0, "需求澄清处理超时"

        return results

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """测试并发会话处理性能"""
        concurrent_sessions = 5
        test_contents = [f"测试需求内容 {i}" for i in range(concurrent_sessions)]

        async def process_session(content: str) -> Tuple[float, str]:
            start_time = time.time()
            result = await AnalysisHandler.analyze_requirement({"content": content})
            session_id = result["session_id"]

            # 模拟澄清过程
            for _ in range(3):
                await ClarificationHandler.process_clarification(
                    session_id=session_id,
                    answer="测试回答",
                )
                await asyncio.sleep(0.1)  # 模拟用户思考时间

            end_time = time.time()
            return end_time - start_time, session_id

        # 并发处理会话
        tasks = [process_session(content) for content in test_contents]
        results = await asyncio.gather(*tasks)

        # 输出性能报告
        print("\n并发会话处理性能测试结果:")
        print("=" * 50)
        print(f"并发会话数: {concurrent_sessions}")
        for i, (processing_time, session_id) in enumerate(results):
            print(f"会话 {i + 1}:")
            print(f"处理时间: {processing_time:.2f}秒")
            print(f"会话ID: {session_id}")
            print("-" * 30)

        # 验证性能指标
        for processing_time, _ in results:
            assert processing_time < 30.0, "并发会话处理超时"

        return results

    @pytest.mark.asyncio
    async def test_workflow_stream_performance(self):
        """测试工作流事件流性能"""
        # 创建测试会话
        content = "需要开发一个在线商城系统"
        result = await AnalysisHandler.analyze_requirement({"content": content})
        session_id = result["session_id"]

        start_time = time.time()
        event_count = 0
        total_processing_time = 0

        async for event in WorkflowHandler.generate_workflow_stream(session_id):
            event_time = time.time()
            event_count += 1

            if event_count > 1:
                # 计算事件间隔时间
                event_interval = event_time - last_event_time
                total_processing_time += event_interval

            last_event_time = event_time

        end_time = time.time()
        total_time = end_time - start_time
        avg_interval = (
            total_processing_time / (event_count - 1) if event_count > 1 else 0
        )

        # 输出性能报告
        print("\n工作流事件流性能测试结果:")
        print("=" * 50)
        print(f"总事件数: {event_count}")
        print(f"总处理时间: {total_time:.2f}秒")
        print(f"平均事件间隔: {avg_interval:.2f}秒")
        print(f"会话ID: {session_id}")

        # 验证性能指标
        assert total_time < 60.0, "工作流处理超时"
        assert avg_interval < 1.0, "事件间隔过长"

        return {
            "event_count": event_count,
            "total_time": total_time,
            "avg_interval": avg_interval,
        }

    def test_session_management_performance(self):
        """测试会话管理性能"""
        # 创建大量测试会话
        session_count = 100
        with ThreadPoolExecutor() as executor:
            session_ids = list(
                executor.map(
                    lambda _: SessionHandler.get_active_sessions(), range(session_count)
                )
            )

        start_time = time.time()
        active_sessions = SessionHandler.get_active_sessions()
        list_time = time.time() - start_time

        # 输出性能报告
        print("\n会话管理性能测试结果:")
        print("=" * 50)
        print(f"会话总数: {session_count}")
        print(f"列表获取时间: {list_time:.2f}秒")
        print(f"活动会话数: {len(active_sessions)}")

        # 验证性能指标
        assert list_time < 1.0, "会话列表获取超时"

        return {
            "session_count": session_count,
            "list_time": list_time,
            "active_count": len(active_sessions),
        }
