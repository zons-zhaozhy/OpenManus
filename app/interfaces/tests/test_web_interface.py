"""
Web界面测试套件
"""

import json
from typing import Dict, List, Optional

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.agent.manus import Manus
from app.interfaces.web_interface import WebInterface


class MockManus:
    """Mock Manus Agent"""

    def __init__(self):
        self.analysis_progress = 0
        self.analysis_metrics = {}

    @classmethod
    async def create(cls):
        """创建Mock Agent"""
        return cls()

    async def analyze_requirements(self, request: str) -> str:
        """模拟需求分析"""
        self.analysis_progress = 50
        self.analysis_metrics = {
            "clarity": 0.8,
            "completeness": 0.7,
            "consistency": 0.9,
        }
        return "需求分析结果"

    def get_analysis_progress(self) -> float:
        """获取分析进度"""
        return self.analysis_progress

    def get_analysis_metrics(self) -> Dict:
        """获取分析指标"""
        return self.analysis_metrics

    async def cleanup(self):
        """清理资源"""
        pass


@pytest.fixture
def mock_manus(monkeypatch):
    """Mock Manus Agent"""
    monkeypatch.setattr("app.interfaces.web_interface.Manus", MockManus)


@pytest.fixture
def test_client(mock_manus):
    """创建测试客户端"""
    interface = WebInterface()
    return TestClient(interface.app)


def test_serve_frontend(test_client):
    """测试前端页面服务"""
    response = test_client.get("/")
    assert response.status_code == 200


def test_chat_endpoint(test_client):
    """测试聊天API端点"""
    # 发送聊天请求
    response = test_client.post(
        "/api/chat",
        json={"message": "我需要一个在线教育平台"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["response"] == "需求分析结果"
    assert data["analysis_progress"] == 50
    assert data["analysis_metrics"] == {
        "clarity": 0.8,
        "completeness": 0.7,
        "consistency": 0.9,
    }

    # 使用相同的session_id继续对话
    session_id = data["session_id"]
    response = test_client.post(
        "/api/chat",
        json={"message": "需要支持视频直播", "session_id": session_id},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == session_id


def test_get_session_history(test_client):
    """测试获取会话历史"""
    # 创建会话
    response = test_client.post(
        "/api/chat",
        json={"message": "我需要一个在线教育平台"},
    )
    session_id = response.json()["session_id"]

    # 获取历史
    response = test_client.get(f"/api/sessions/{session_id}/history")
    assert response.status_code == 200

    data = response.json()
    assert len(data["history"]) == 2  # 用户消息和助手回复
    assert data["analysis_progress"] == 50
    assert data["analysis_metrics"] == {
        "clarity": 0.8,
        "completeness": 0.7,
        "consistency": 0.9,
    }


def test_delete_session(test_client):
    """测试删除会话"""
    # 创建会话
    response = test_client.post(
        "/api/chat",
        json={"message": "我需要一个在线教育平台"},
    )
    session_id = response.json()["session_id"]

    # 删除会话
    response = test_client.delete(f"/api/sessions/{session_id}")
    assert response.status_code == 200

    # 验证会话已删除
    response = test_client.get(f"/api/sessions/{session_id}/history")
    assert response.status_code == 404


def test_extract_suggestions(test_client):
    """测试建议问题提取"""
    interface = WebInterface()
    suggestions = interface.extract_suggestions(
        """
        1. 您需要支持哪些类型的课程？
        2. 是否需要实时互动功能？
        3. 对于用户角色有什么要求？
        这个系统需要支持多少并发用户？
        您对数据安全有什么特殊要求吗？
        简单的问题。
        """
    )
    assert len(suggestions) == 5
    assert "您需要支持哪些类型的课程？" in suggestions
    assert "是否需要实时互动功能？" in suggestions
    assert "对于用户角色有什么要求？" in suggestions
    assert "这个系统需要支持多少并发用户？" in suggestions
    assert "您对数据安全有什么特殊要求吗？" in suggestions
