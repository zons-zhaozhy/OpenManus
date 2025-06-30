#!/usr/bin/env python3
"""
OpenManus - 统一入口点
支持多种运行模式：CLI交互、Web GUI、单次执行
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import click
from rich import print

from app.agent.manus import Manus
from app.config import Config, DialogueConfig, config
from app.logger import logger


class OpenManusRunner:
    """OpenManus统一运行器"""

    def __init__(self):
        self.agent: Optional[Manus] = None

    async def initialize_agent(self, manus_config: Optional[Dict] = None) -> Manus:
        """初始化Agent"""
        if not self.agent:
            if manus_config is None:
                manus_config = {
                    "dialogue": DialogueConfig(
                        min_rounds=1,
                        max_rounds=10,
                        auto_extend=True,
                        extend_threshold=0.8,
                    )
                }
            self.agent = Manus(config=manus_config)
            await self.agent.initialize()
        return self.agent

    async def cleanup(self):
        """清理资源"""
        if self.agent:
            await self.agent.cleanup()

    async def run_once(self, request: str) -> str:
        """单次执行模式"""
        try:
            print(f"🎯 处理需求: {request}")

            # 创建工作目录
            workspace_dir = Path("workspace")
            workspace_dir.mkdir(exist_ok=True)

            # 初始化并运行分析
            agent = await self.initialize_agent()
            result = await agent.analyze_requirements(request)

            # 保存分析报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = workspace_dir / f"Requirements_Analysis_{timestamp}.md"
            report_file.write_text(result, encoding="utf-8")

            print(f"需求分析报告已保存至：{report_file}")
            print("✅ 分析完成:")
            print(result)

            return result

        except Exception as e:
            error_msg = f"运行错误: {str(e)}"
            logging.error(error_msg)
            print(f"❌ {error_msg}")
            return error_msg

    async def run_interactive_cli(self):
        """交互式CLI模式"""
        from app.interfaces.cli_interface import CLIInterface

        try:
            print("🚀 启动交互式CLI模式")
            interface = CLIInterface()
            agent = await self.initialize_agent()
            await interface.run(agent)

        except Exception as e:
            error_msg = f"CLI模式运行错误: {str(e)}"
            logging.error(error_msg)
            print(f"❌ {error_msg}")

    async def run_web_gui(self, host: str = "0.0.0.0", port: int = 3000):
        """Web GUI模式"""
        from app.interfaces.web_interface import WebInterface

        try:
            print(f"🌐 启动Web GUI模式 - http://{host}:{port}")
            interface = WebInterface()
            agent = await self.initialize_agent()
            await interface.run(host=host, port=port)

        except Exception as e:
            error_msg = f"Web GUI模式运行错误: {str(e)}"
            logging.error(error_msg)
            print(f"❌ {error_msg}")


@click.command()
@click.option("--mode", default="web", help="运行模式: web/cli/once")
@click.option("--port", default=3000, help="Web服务端口")
@click.option("--host", default="127.0.0.1", help="Web服务主机")
@click.argument("requirement", required=False)
def main(mode: str, port: int, host: str, requirement: str = None) -> None:
    """OpenManus主入口"""
    runner = OpenManusRunner()

    try:
        if mode == "once" and requirement:
            asyncio.run(runner.run_once(requirement))
        elif mode == "cli":
            asyncio.run(runner.run_interactive_cli())
        elif mode == "web":
            asyncio.run(runner.run_web_gui(host=host, port=port))
        else:
            print("⚠️ 请选择正确的运行模式:")
            print(
                "1. Web GUI模式: python main.py --mode web [--host HOST] [--port PORT]"
            )
            print("2. 交互式CLI: python main.py --mode cli")
            print('3. 单次执行: python main.py --mode once "开发一个在线教育平台"')
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 感谢使用OpenManus，再见！")
    except Exception as e:
        print(f"❌ 运行错误: {str(e)}")
        sys.exit(1)
    finally:
        asyncio.run(runner.cleanup())


if __name__ == "__main__":
    main()
