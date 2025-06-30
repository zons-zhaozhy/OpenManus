"""
CLI界面测试套件
"""

import asyncio
from typing import Dict, List, Optional

import pytest
from pytest_mock import MockerFixture

from app.agent.manus import Manus
from app.interfaces.cli_interface import CLIInterface
from app.schema import (
    ChoiceQuestion,
    ConfirmQuestion,
    MultiChoiceQuestion,
    Question,
    QuestionResponse,
    QuestionType,
    QuestionUnion,
    ScaleQuestion,
    ShortTextQuestion,
    YesNoQuestion,
)


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
    monkeypatch.setattr("app.interfaces.cli_interface.Manus", MockManus)


@pytest.fixture
def cli_interface():
    """创建CLI界面实例"""
    return CLIInterface()


def test_parse_question(cli_interface):
    """测试问题解析"""
    # 选择题
    question_json = {
        "type": "choice",
        "question": "选择系统类型",
        "options": ["Web应用", "移动应用", "桌面应用"],
        "default": 0,
    }
    question = cli_interface.parse_question(str(question_json))
    assert isinstance(question, ChoiceQuestion)
    assert question.question == "选择系统类型"
    assert len(question.options) == 3

    # 多选题
    question_json = {
        "type": "multi_choice",
        "question": "选择功能模块",
        "options": ["用户管理", "内容管理", "数据分析"],
        "defaults": [0, 1],
    }
    question = cli_interface.parse_question(str(question_json))
    assert isinstance(question, MultiChoiceQuestion)
    assert question.question == "选择功能模块"
    assert len(question.options) == 3

    # 是否题
    question_json = {
        "type": "yes_no",
        "question": "是否需要多语言支持",
        "default": True,
    }
    question = cli_interface.parse_question(str(question_json))
    assert isinstance(question, YesNoQuestion)
    assert question.question == "是否需要多语言支持"
    assert question.default is True


def test_format_question(cli_interface):
    """测试问题格式化"""
    # 选择题
    question = ChoiceQuestion(
        type=QuestionType.CHOICE,
        question="选择系统类型",
        options=["Web应用", "移动应用", "桌面应用"],
        default=0,
    )
    formatted = cli_interface.format_question(question)
    assert "选择系统类型" in formatted
    assert "Web应用" in formatted
    assert "(默认)" in formatted

    # 多选题
    question = MultiChoiceQuestion(
        type=QuestionType.MULTI_CHOICE,
        question="选择功能模块",
        options=["用户管理", "内容管理", "数据分析"],
        defaults=[0, 1],
    )
    formatted = cli_interface.format_question(question)
    assert "选择功能模块" in formatted
    assert "用户管理" in formatted
    assert "(默认)" in formatted

    # 是否题
    question = YesNoQuestion(
        type=QuestionType.YES_NO,
        question="是否需要多语言支持",
        default=True,
    )
    formatted = cli_interface.format_question(question)
    assert "是否需要多语言支持" in formatted
    assert "(默认是)" in formatted


def test_parse_answer(cli_interface):
    """测试答案解析"""
    # 选择题
    question = ChoiceQuestion(
        type=QuestionType.CHOICE,
        question="选择系统类型",
        options=["Web应用", "移动应用", "桌面应用"],
        default=0,
    )
    response = cli_interface.parse_answer(question, "2")
    assert response.response == 1  # 0-based index

    # 多选题
    question = MultiChoiceQuestion(
        type=QuestionType.MULTI_CHOICE,
        question="选择功能模块",
        options=["用户管理", "内容管理", "数据分析"],
        defaults=[0, 1],
    )
    response = cli_interface.parse_answer(question, "1,3")
    assert response.response == [0, 2]  # 0-based indices

    # 是否题
    question = YesNoQuestion(
        type=QuestionType.YES_NO,
        question="是否需要多语言支持",
        default=True,
    )
    response = cli_interface.parse_answer(question, "y")
    assert response.response is True


@pytest.mark.asyncio
async def test_process_user_input(cli_interface, mock_manus):
    """测试用户输入处理"""
    agent = await MockManus.create()

    # 正常输入
    result = await cli_interface.process_user_input(agent, "我需要一个在线教育平台")
    assert result is True

    # 帮助命令
    result = await cli_interface.process_user_input(agent, "/help")
    assert result is True

    # 退出命令
    result = await cli_interface.process_user_input(agent, "/exit")
    assert result is False


def test_show_conversation_summary(cli_interface):
    """测试对话总结显示"""
    cli_interface.conversation_history = [
        {"role": "user", "content": "我需要一个在线教育平台"},
        {"role": "assistant", "content": "需求分析结果"},
    ]
    cli_interface.show_conversation_summary()  # 验证不抛出异常


@pytest.mark.asyncio
async def test_generate_document(cli_interface, mock_manus):
    """测试文档生成"""
    agent = await MockManus.create()
    await cli_interface.generate_document(agent)  # 验证不抛出异常
