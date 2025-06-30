"""
主入口测试套件
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional

import pytest
from click.testing import CliRunner

from app.agent.manus import Manus
from app.interfaces.cli_interface import CLIInterface
from app.interfaces.web_interface import WebInterface
from main import OpenManusRunner, main


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

    async def initialize(self):
        """初始化Agent"""
        pass

    async def cleanup(self):
        """清理资源"""
        pass


@pytest.fixture
def mock_manus(monkeypatch):
    """Mock Manus Agent"""
    monkeypatch.setattr("main.Manus", MockManus)


@pytest.fixture
def runner():
    """创建CLI测试运行器"""
    return CliRunner()


@pytest.fixture
def openmanus_runner():
    """创建OpenManus运行器"""
    return OpenManusRunner()


@pytest.mark.asyncio
async def test_initialize_agent(openmanus_runner):
    """测试Agent初始化"""
    agent = await openmanus_runner.initialize_agent()
    assert agent is not None
    assert isinstance(agent, MockManus)


@pytest.mark.asyncio
async def test_run_once(openmanus_runner, tmp_path):
    """测试单次执行模式"""
    # 设置工作目录
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()

    # 运行分析
    result = await openmanus_runner.run_once("我需要一个在线教育平台")
    assert result == "需求分析结果"

    # 验证报告文件
    report_files = list(workspace_dir.glob("Requirements_Analysis_*.md"))
    assert len(report_files) == 1


@pytest.mark.asyncio
async def test_run_interactive_cli(openmanus_runner, monkeypatch):
    """测试交互式CLI模式"""

    # Mock CLIInterface
    class MockCLIInterface:
        async def run(self, agent):
            pass

    monkeypatch.setattr("main.CLIInterface", MockCLIInterface)
    await openmanus_runner.run_interactive_cli()


@pytest.mark.asyncio
async def test_run_web_gui(openmanus_runner, monkeypatch):
    """测试Web GUI模式"""

    # Mock WebInterface
    class MockWebInterface:
        async def run(self, host, port):
            pass

    monkeypatch.setattr("main.WebInterface", MockWebInterface)
    await openmanus_runner.run_web_gui(host="127.0.0.1", port=3000)


def test_main_once_mode(runner, mock_manus):
    """测试主入口单次执行模式"""
    result = runner.invoke(main, ["--mode", "once", "我需要一个在线教育平台"])
    assert result.exit_code == 0


def test_main_cli_mode(runner, mock_manus):
    """测试主入口CLI模式"""
    result = runner.invoke(main, ["--mode", "cli"])
    assert result.exit_code == 0


def test_main_web_mode(runner, mock_manus):
    """测试主入口Web模式"""
    result = runner.invoke(
        main, ["--mode", "web", "--host", "127.0.0.1", "--port", "3000"]
    )
    assert result.exit_code == 0


def test_main_invalid_mode(runner):
    """测试主入口无效模式"""
    result = runner.invoke(main, ["--mode", "invalid"])
    assert result.exit_code == 1
