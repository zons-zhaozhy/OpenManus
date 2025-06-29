#!/usr/bin/env python3
"""
综合测试澄清功能
测试澄清功能的各个方面，包括：
1. 异步调用
2. 状态管理
3. 错误处理
4. 性能表现
5. 资源管理
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.types import AgentState
from app.core.state_manager import StateManager
from app.api.requirements_modular.handlers.clarification_handler import ClarificationHandler

# 测试数据
TEST_REQUIREMENTS = [
    {
        "type": "education",
        "content": "需要一个在线教育平台，主要功能包括课程管理、学生管理和在线考试。",
        "expected_points": ["用户角色", "并发需求", "数据安全"]
    },
    {
        "type": "ecommerce",
        "content": "需要一个电商平台，支持商品管理、订单处理和支付功能。",
        "expected_points": ["支付方式", "库存管理", "用户体系"]
    },
    {
        "type": "social",
        "content": "开发一个社交媒体平台，支持用户发帖、评论和私信。",
        "expected_points": ["信息安全", "用户隐私", "消息推送"]
    }
]

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def clarification_handler():
    handler = ClarificationHandler()
    await handler.initialize()
    yield handler
    # 清理资源
    for session_id in list(handler._sessions.keys()):
        await handler.cleanup_session(session_id)

@pytest.fixture
async def state_manager():
    manager = StateManager()
    await manager.initialize()
    yield manager
    await manager.cleanup()

class TestClarificationFlow:
    """测试澄清流程"""

    @pytest.mark.asyncio
    async def test_basic_flow(self, async_client, clarification_handler):
        """测试基本流程"""
        # 1. 创建会话
        session_id = str(uuid.uuid4())
        requirement = TEST_REQUIREMENTS[0]

        # 2. 生成问题
        response = await async_client.post(
            "/api/clarification/question",
            json={
                "session_id": session_id,
                "requirement": requirement["content"],
                "context": {"type": requirement["type"]}
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert "questions" in result
        assert len(result["questions"]) > 0

        # 3. 处理答案
        response = await async_client.post(
            "/api/clarification/answer",
            json={
                "session_id": session_id,
                "requirement": "平台需要支持1000个并发用户，主要面向高校师生。",
                "context": {"type": requirement["type"]}
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status"] in ["complete", "in_progress"]

        # 4. 检查状态
        response = await async_client.get(f"/api/clarification/status/{session_id}")
        assert response.status_code == 200
        status = response.json()
        assert status["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_error_handling(self, async_client):
        """测试错误处理"""
        # 1. 测试无效会话
        response = await async_client.get("/api/clarification/status/invalid_session")
        assert response.status_code == 500
        assert "会话不存在" in response.json()["detail"]

        # 2. 测试无效请求
        response = await async_client.post(
            "/api/clarification/answer",
            json={"invalid": "data"}
        )
        assert response.status_code in [400, 422]

        # 3. 测试空需求
        response = await async_client.post(
            "/api/clarification/question",
            json={
                "session_id": str(uuid.uuid4()),
                "requirement": "",
                "context": {}
            }
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_state_management(self, async_client, state_manager):
        """测试状态管理"""
        session_id = str(uuid.uuid4())
        agent_id = f"clarifier_{session_id}"

        # 1. 检查初始状态
        state = await state_manager.get_agent_state(agent_id)
        assert state["state"] == AgentState.UNKNOWN

        # 2. 发送请求并检查状态变化
        response = await async_client.post(
            "/api/clarification/question",
            json={
                "session_id": session_id,
                "requirement": TEST_REQUIREMENTS[0]["content"],
                "context": {"agent_id": agent_id}
            }
        )
        assert response.status_code == 200

        # 3. 检查状态历史
        history = await state_manager.get_agent_history(agent_id)
        assert len(history) > 0
        assert any(h["state"] == AgentState.COMPLETED for h in history)

    @pytest.mark.asyncio
    async def test_performance(self, async_client):
        """测试性能"""
        # 1. 准备并发请求
        session_ids = [str(uuid.uuid4()) for _ in range(5)]
        requests = []

        start_time = time.time()

        # 2. 发送并发请求
        for session_id in session_ids:
            requests.append(
                async_client.post(
                    "/api/clarification/question",
                    json={
                        "session_id": session_id,
                        "requirement": TEST_REQUIREMENTS[0]["content"],
                        "context": {"type": "education"}
                    }
                )
            )

        # 3. 等待所有请求完成
        responses = await asyncio.gather(*requests)
        
        elapsed_time = time.time() - start_time
        print(f"5个并发请求耗时: {elapsed_time:.2f}秒")

        # 4. 验证结果
        for response in responses:
            assert response.status_code == 200
            result = response.json()
            assert "questions" in result

        # 5. 检查性能指标
        assert elapsed_time < 10.0  # 假设我们期望5个请求在10秒内完成

    @pytest.mark.asyncio
    async def test_resource_management(self, async_client, clarification_handler):
        """测试资源管理"""
        # 1. 创建多个会话
        sessions = []
        for _ in range(3):
            session_id = str(uuid.uuid4())
            response = await async_client.post(
                "/api/clarification/question",
                json={
                    "session_id": session_id,
                    "requirement": TEST_REQUIREMENTS[0]["content"],
                    "context": {"type": "education"}
                }
            )
            assert response.status_code == 200
            sessions.append(session_id)

        # 2. 检查资源使用
        assert len(clarification_handler._sessions) >= len(sessions)
        assert len(clarification_handler._session_locks) >= len(sessions)

        # 3. 清理会话
        for session_id in sessions:
            await clarification_handler.cleanup_session(session_id)

        # 4. 验证清理结果
        for session_id in sessions:
            assert session_id not in clarification_handler._sessions
            assert session_id not in clarification_handler._session_locks

    @pytest.mark.asyncio
    async def test_comprehensive_flow(self, async_client):
        """综合测试完整流程"""
        session_id = str(uuid.uuid4())
        requirement = TEST_REQUIREMENTS[1]  # 使用电商平台需求

        # 1. 初始化会话
        response = await async_client.post(
            "/api/clarification/question",
            json={
                "session_id": session_id,
                "requirement": requirement["content"],
                "context": {"type": requirement["type"]}
            }
        )
        assert response.status_code == 200
        result = response.json()
        questions = result["questions"]
        assert len(questions) > 0

        # 2. 多轮澄清
        answers = [
            "平台主要面向个人消费者，支持微信和支付宝支付。",
            "需要完整的会员体系，支持积分和优惠券。",
            "商品管理需要支持多规格和多库位。"
        ]

        for answer in answers:
            response = await async_client.post(
                "/api/clarification/answer",
                json={
                    "session_id": session_id,
                    "requirement": answer,
                    "context": {"type": requirement["type"]}
                }
            )
            assert response.status_code == 200
            result = response.json()
            
            # 检查状态
            status_response = await async_client.get(
                f"/api/clarification/status/{session_id}"
            )
            assert status_response.status_code == 200

        # 3. 验证最终状态
        final_status = await async_client.get(f"/api/clarification/status/{session_id}")
        assert final_status.status_code == 200
        status_data = final_status.json()
        assert "is_complete" in status_data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
