"""
需求分析模块单元测试
"""

import pytest
from fastapi import HTTPException

from app.api.requirements_modular.handlers.analysis_handler import AnalysisHandler
from app.api.requirements_modular.handlers.clarification_handler import (
    ClarificationHandler,
)
from app.api.requirements_modular.handlers.session_handler import SessionHandler
from app.api.requirements_modular.storage import session_storage


@pytest.fixture
def session_handler():
    """创建会话处理程序实例"""
    return SessionHandler()


@pytest.fixture
def analysis_handler():
    """创建分析处理程序实例"""
    return AnalysisHandler()


@pytest.fixture
def clarification_handler():
    """创建澄清处理程序实例"""
    return ClarificationHandler()


@pytest.fixture
def mock_session():
    """模拟会话数据"""
    session_id = "test_session"
    session_data = {
        "id": session_id,
        "round_count": 2,
        "status": "clarifying",
        "context": {"key": "value"},
    }
    session_storage.set_session(session_id, session_data)
    yield session_id
    session_storage.delete_session(session_id)


async def test_get_session(session_handler, mock_session):
    """测试获取会话信息"""
    result = await session_handler.get_session(mock_session)
    assert result["id"] == mock_session
    assert result["status"] == "clarifying"


async def test_get_invalid_session(session_handler):
    """测试获取无效会话"""
    result = await session_handler.get_session("invalid_session")
    assert "error" in result


async def test_get_session_progress(session_handler, mock_session):
    """测试获取会话进度"""
    result = await session_handler.get_progress(mock_session)
    assert result["percentage"] == 40  # 2/5 * 100
    assert result["current_stage"] == "澄清中"
    assert result["round_count"] == 2


async def test_get_active_sessions(session_handler, mock_session):
    """测试获取活跃会话列表"""
    result = await session_handler.get_active_sessions()
    assert "active_sessions" in result
    assert mock_session in result["active_sessions"]
