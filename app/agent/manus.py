"""
Manus agent implementation
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import Field, model_validator

from app.agent.browser import BrowserContextHelper
from app.agent.dialogue_context import DialogueContext
from app.agent.toolcall import ToolCallAgent
from app.config import DialogueConfig, config
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.schema import (
    ChoiceQuestion,
    ConfirmQuestion,
    MultiChoiceQuestion,
    Question,
    QuestionType,
    ScaleQuestion,
    ShortTextQuestion,
    YesNoQuestion,
)
from app.tool import Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute
from app.tool.requirements_analyzer import RequirementsAnalyzer
from app.tool.requirements_reviewer import RequirementsReviewer, ReviewResult
from app.tool.str_replace_editor import StrReplaceEditor


@dataclass
class DialogueContext:
    """对话上下文"""

    history: List[Dict[str, Any]] = field(default_factory=list)
    current_question: Optional[str] = None
    pending_clarifications: List[str] = field(default_factory=list)
    accumulated_requirements: Dict[str, List[str]] = field(default_factory=dict)

    def add_user_response(self, question: str, answer: str) -> None:
        """添加用户回答"""
        self.history.append(
            {"question": question, "answer": answer, "timestamp": time.time()}
        )

    def add_request(self, request: str) -> None:
        """添加用户请求"""
        self.history.append(
            {"type": "request", "content": request, "timestamp": time.time()}
        )

    def add_clarification(self, point: str, response: str) -> None:
        """添加澄清信息"""
        if point not in self.accumulated_requirements:
            self.accumulated_requirements[point] = []
        self.accumulated_requirements[point].append(response)

        self.history.append(
            {
                "type": "clarification",
                "point": point,
                "content": response,
                "timestamp": time.time(),
            }
        )

    def get_point_details(self, point: str) -> List[str]:
        """获取某个点的所有细节"""
        return self.accumulated_requirements.get(point, [])

    def get_full_context(self) -> Dict[str, Any]:
        """获取完整上下文"""
        return {
            "history": self.history,
            "requirements": self.accumulated_requirements,
            "pending": self.pending_clarifications,
        }


class Manus(ToolCallAgent):
    """A versatile general-purpose agent with support for both local and MCP tools."""

    name: str = "Manus"
    description: str = (
        "A versatile agent that can solve various tasks using multiple tools including MCP-based tools"
    )

    system_prompt: str = SYSTEM_PROMPT.format(directory=config.workspace_root)
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 10000
    max_steps: int = 20

    # MCP clients for remote tool access
    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    # Add general-purpose tools to the tool collection
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            RequirementsAnalyzer(),
            PythonExecute(),
            BrowserUseTool(),
            StrReplaceEditor(),
            AskHuman(),
            Terminate(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
    browser_context_helper: Optional[BrowserContextHelper] = None

    # Track connected MCP servers
    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )  # server_id -> url/command
    _initialized: bool = False

    # 新增：对话控制相关属性
    is_waiting_response: bool = False
    current_question: Optional[Question] = None
    dialogue_context: DialogueContext = Field(default_factory=DialogueContext)
    dialogue_config: DialogueConfig = Field(default_factory=DialogueConfig)
    current_round: int = 0

    def __init__(self):
        super().__init__()
        self.dialogue_context = DialogueContext()
        self.analyzer = RequirementsAnalyzer()
        self.requirements_reviewer = None  # Will be initialized later

    async def initialize(self) -> None:
        """初始化组件"""
        self.requirements_reviewer = RequirementsReviewer()

    def create_choice_question(
        self,
        question: str,
        options: List[str],
        description: Optional[str] = None,
        default: Optional[int] = None,
    ) -> str:
        """创建选择题"""
        q = ChoiceQuestion(
            question=question, options=options, description=description, default=default
        )
        return json.dumps(q.model_dump(), ensure_ascii=False)

    def create_multi_choice_question(
        self,
        question: str,
        options: List[str],
        description: Optional[str] = None,
        defaults: Optional[List[int]] = None,
    ) -> str:
        """创建多选题"""
        q = MultiChoiceQuestion(
            question=question,
            options=options,
            description=description,
            defaults=defaults,
        )
        return json.dumps(q.model_dump(), ensure_ascii=False)

    def create_yes_no_question(
        self,
        question: str,
        description: Optional[str] = None,
        default: Optional[bool] = None,
    ) -> str:
        """创建是/否问题"""
        q = YesNoQuestion(question=question, description=description, default=default)
        return json.dumps(q.model_dump(), ensure_ascii=False)

    def create_scale_question(
        self,
        question: str,
        min_value: int = 1,
        max_value: int = 5,
        labels: Optional[List[str]] = None,
        description: Optional[str] = None,
        default: Optional[int] = None,
    ) -> str:
        """创建量表问题"""
        q = ScaleQuestion(
            question=question,
            min_value=min_value,
            max_value=max_value,
            labels=labels,
            description=description,
            default=default,
        )
        return json.dumps(q.model_dump(), ensure_ascii=False)

    def create_short_text_question(
        self,
        question: str,
        max_length: Optional[int] = None,
        placeholder: Optional[str] = None,
        description: Optional[str] = None,
        default: Optional[str] = None,
    ) -> str:
        """创建简短文本问题"""
        q = ShortTextQuestion(
            question=question,
            max_length=max_length,
            placeholder=placeholder,
            description=description,
            default=default,
        )
        return json.dumps(q.model_dump(), ensure_ascii=False)

    def create_confirm_question(
        self,
        question: str,
        default_value: str,
        description: Optional[str] = None,
        default: bool = True,
    ) -> str:
        """创建确认问题"""
        q = ConfirmQuestion(
            question=question,
            default_value=default_value,
            description=description,
            default=default,
        )
        return json.dumps(q.model_dump(), ensure_ascii=False)

    async def process_response(self, response: str) -> Tuple[str, bool]:
        """处理回复，返回处理后的回复和是否需要等待用户输入"""
        # 检查是否包含JSON格式的问题
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                question_json = response[start:end]
                json.loads(question_json)  # 验证JSON格式
                self.is_waiting_response = True
                return response, True
        except:
            pass

        self.is_waiting_response = False
        return response, False

    def should_continue_dialogue(self) -> bool:
        """判断是否应该继续对话"""
        # 未达到最小轮数
        if self.current_round < self.dialogue_config.min_rounds:
            return True

        # 已达到最大轮数
        if self.current_round >= self.dialogue_config.max_rounds:
            return False

        # 检查是否需要自动延长
        if not self.dialogue_config.auto_extend:
            return False

        # 计算完成度
        completion_rate = self.analyzer.calculate_completion_rate(self.dialogue_context)

        # 如果完成度低于阈值，继续对话
        return completion_rate < self.dialogue_config.extend_threshold

    async def run(self, request: str) -> str:
        """重写run方法以支持动态对话轮数"""
        # 更新上下文
        self.dialogue_context.add_request(request)
        self.current_round += 1

        # 分析当前状态
        analysis = self.analyzer.analyze(self.dialogue_context)

        # 检查是否应该继续对话
        if not self.should_continue_dialogue():
            return self.generate_final_report()

        if analysis.needs_clarification:
            # 使用ask_human获取用户回答
            response = await self.ask_human(analysis.question)
            self.dialogue_context.add_clarification(analysis.point, response)
            # 返回确认信息
            return self.format_clarification_summary()

        # 生成完整分析报告
        return self.generate_analysis_report()

    def generate_final_report(self) -> str:
        """生成最终报告"""
        report = ["# 需求分析最终报告"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report.append(f"\n生成时间：{timestamp}")

        # 添加完成度信息
        completion_rate = self.analyzer.calculate_completion_rate(self.dialogue_context)
        report.append(f"\n## 需求完成度: {completion_rate*100:.1f}%")

        # 添加执行摘要
        report.append("\n## 执行摘要")
        report.append("本报告基于与用户的交互对话，采用结构化方法收集和分析需求。")
        report.append(f"共进行了{self.current_round}轮对话，")
        report.append(f"覆盖了{len(self.analyzer.clarification_points)}个关键分析点。")

        # 添加已收集的信息
        report.append("\n## 详细需求")
        report.extend(self.generate_analysis_report().split("\n"))

        # 添加质量评估
        quality_report = self.analyzer.analyze_document_quality(self.dialogue_context)
        report.append("\n## 质量评估")

        # 添加质量指标
        report.append("\n### 质量指标")
        metrics = quality_report.metrics
        report.extend(
            [
                f"- 完整性: {metrics.completeness*100:.1f}%",
                f"- 清晰度: {metrics.clarity*100:.1f}%",
                f"- 一致性: {metrics.consistency*100:.1f}%",
                f"- 可测试性: {metrics.testability*100:.1f}%",
                f"- 总体评分: {metrics.get_overall_score()*100:.1f}%",
            ]
        )

        # 添加问题列表
        if quality_report.issues:
            report.append("\n### 发现的问题")
            for issue in quality_report.issues:
                report.append(f"- {issue}")

        # 添加改进建议
        if quality_report.suggestions:
            report.append("\n### 改进建议")
            for suggestion in quality_report.suggestions:
                report.append(f"- {suggestion}")

        # 添加风险分析
        report.append("\n## 风险分析")
        if completion_rate < 1:
            report.append("\n### 未完全澄清的点")
            for point in self.analyzer.get_incomplete_points(self.dialogue_context):
                report.append(f"- {point}")

        # 添加建议
        report.append("\n## 建议")
        report.append("基于当前需求分析结果，建议：")
        if completion_rate < 0.8:
            report.append("1. 进一步澄清关键需求点")
            report.append("2. 重点关注未完成的部分")
            report.append("3. 考虑增加对话轮次以提高完整性")
        else:
            report.append("1. 定期回顾需求以确保与业务目标一致")
            report.append("2. 建立需求变更管理机制")
            report.append("3. 进行原型验证以确认需求准确性")

        # 添加后续步骤
        report.append("\n## 后续步骤")
        report.append("1. 需求评审：组织相关方进行需求评审")
        report.append("2. 优先级排序：确定需求实现的优先顺序")
        report.append("3. 技术评估：评估技术可行性和实现成本")
        report.append("4. 项目规划：制定详细的项目实施计划")

        # 保存报告
        report_content = "\n".join(report)
        self.save_report(report_content)

        return report_content

    def save_report(self, content: str) -> None:
        """保存需求分析报告"""
        # 确保workspace目录存在
        workspace_dir = Path("workspace")
        workspace_dir.mkdir(exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Requirements_Analysis_{timestamp}.md"
        filepath = workspace_dir / filename

        # 保存文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"需求分析报告已保存至：{filepath}")

    def format_clarification_summary(self) -> str:
        context = self.dialogue_context.get_full_context()
        summary = ["[已知信息]"]

        for point, details in context["requirements"].items():
            summary.append(f"- {point}:")
            for detail in details:
                summary.append(f"  * {detail}")

        if context["pending"]:
            summary.append("\n[待澄清点]")
            for point in context["pending"]:
                summary.append(f"- {point}")

        return "\n".join(summary)

    def generate_analysis_report(self) -> str:
        context = self.dialogue_context.get_full_context()
        # 生成最终的需求分析报告
        report = ["# 需求分析报告"]

        # 添加项目概述
        report.append("\n## 项目概述")
        if "project_scope" in context["requirements"]:
            report.extend(context["requirements"]["project_scope"])

        # 添加用户角色
        report.append("\n## 用户角色")
        if "user_roles" in context["requirements"]:
            report.extend(context["requirements"]["user_roles"])

        # 添加核心功能
        report.append("\n## 核心功能")
        if "core_features" in context["requirements"]:
            report.extend(context["requirements"]["core_features"])

        # 添加约束条件
        report.append("\n## 约束条件")
        if "constraints" in context["requirements"]:
            report.extend(context["requirements"]["constraints"])

        # 添加成功标准
        report.append("\n## 成功标准")
        if "success_criteria" in context["requirements"]:
            report.extend(context["requirements"]["success_criteria"])

        return "\n".join(report)

    @model_validator(mode="after")
    def initialize_helper(self) -> "Manus":
        """Initialize basic components synchronously."""
        self.browser_context_helper = BrowserContextHelper(self)
        self.requirements_reviewer = RequirementsReviewer()
        return self

    @classmethod
    async def create(cls, **kwargs) -> "Manus":
        """Factory method to create and properly initialize a Manus instance."""
        instance = cls(**kwargs)
        await instance.initialize_mcp_servers()
        instance._initialized = True
        return instance

    async def initialize_mcp_servers(self) -> None:
        """Initialize connections to configured MCP servers."""
        if (
            not hasattr(config, "mcp_config")
            or not config.mcp_config
            or not config.mcp_config.servers
        ):
            logger.info("No MCP servers configured, skipping initialization")
            return

        for server_id, server_config in config.mcp_config.servers.items():
            try:
                # Skip if server config is incomplete
                if not server_config or not server_config.type:
                    logger.warning(
                        f"Incomplete configuration for MCP server {server_id}, skipping"
                    )
                    continue

                if server_config.type == "sse":
                    if not server_config.url:
                        logger.warning(
                            f"Missing URL for SSE server {server_id}, skipping"
                        )
                        continue
                    try:
                        await self.connect_mcp_server(server_config.url, server_id)
                        logger.info(
                            f"Connected to MCP server {server_id} at {server_config.url}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to connect to SSE server {server_id}: {e}"
                        )
                        continue

                elif server_config.type == "stdio":
                    if not server_config.command:
                        logger.warning(
                            f"Missing command for stdio server {server_id}, skipping"
                        )
                        continue
                    try:
                        await self.connect_mcp_server(
                            server_config.command,
                            server_id,
                            use_stdio=True,
                            stdio_args=server_config.args,
                        )
                        logger.info(
                            f"Connected to MCP server {server_id} using command {server_config.command}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to connect to stdio server {server_id}: {e}"
                        )
                        continue
                else:
                    logger.warning(
                        f"Unsupported server type {server_config.type} for server {server_id}, skipping"
                    )

            except Exception as e:
                logger.error(
                    f"Unexpected error initializing MCP server {server_id}: {e}"
                )

    async def connect_mcp_server(
        self,
        server_url: str,
        server_id: str = "",
        use_stdio: bool = False,
        stdio_args: List[str] = None,
    ) -> None:
        """Connect to an MCP server and add its tools."""
        if use_stdio:
            await self.mcp_clients.connect_stdio(
                server_url, stdio_args or [], server_id
            )
            self.connected_servers[server_id or server_url] = server_url
        else:
            await self.mcp_clients.connect_sse(server_url, server_id)
            self.connected_servers[server_id or server_url] = server_url

        # Update available tools with only the new tools from this server
        new_tools = [
            tool for tool in self.mcp_clients.tools if tool.server_id == server_id
        ]
        self.available_tools.add_tools(*new_tools)

    async def disconnect_mcp_server(self, server_id: str = "") -> None:
        """Disconnect from an MCP server and remove its tools."""
        await self.mcp_clients.disconnect(server_id)
        if server_id:
            self.connected_servers.pop(server_id, None)
        else:
            self.connected_servers.clear()

        # Rebuild available tools without the disconnected server's tools
        base_tools = [
            tool
            for tool in self.available_tools.tools
            if not isinstance(tool, MCPClientTool)
        ]
        self.available_tools = ToolCollection(*base_tools)
        self.available_tools.add_tools(*self.mcp_clients.tools)

    async def cleanup(self):
        """Clean up Manus agent resources."""
        if self.browser_context_helper:
            await self.browser_context_helper.cleanup_browser()
        # Disconnect from all MCP servers only if we were initialized
        if self._initialized:
            await self.disconnect_mcp_server()
            self._initialized = False

    async def think(self) -> bool:
        """Process current state and decide next actions with appropriate context."""
        if not self._initialized:
            await self.initialize_mcp_servers()
            self._initialized = True

        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.name == BrowserUseTool().name
            for msg in recent_messages
            if msg.tool_calls
            for tc in msg.tool_calls
        )

        if browser_in_use:
            self.next_step_prompt = (
                await self.browser_context_helper.format_next_step_prompt()
            )

        result = await super().think()

        # Restore original prompt
        self.next_step_prompt = original_prompt

        return result

    async def analyze_requirements(
        self,
        user_input: str,
        export_format: str = "markdown",
        save_to_file: bool = True,
        output_dir: str = "reports",
        batch_export: bool = False,
        include_history: bool = True,
    ) -> str:
        """分析需求

        Args:
            user_input: 用户输入
            export_format: 导出格式，支持 "markdown" 或 "html"
            save_to_file: 是否保存到文件系统
            output_dir: 输出目录，默认为 "reports"
            batch_export: 是否导出历史评审结果，默认为 False
            include_history: 是否在批量导出时包含历史记录，默认为 True

        Returns:
            str: 分析报告
        """
        try:
            # 使用需求分析器分析用户输入
            analysis_result = await self.analyzer.analyze_user_input(
                user_input, self.dialogue_context
            )

            # 进行需求评审
            review_result = await self.requirements_reviewer.review_requirements(
                self.dialogue_context.accumulated_requirements
            )

            # 如果需要批量导出
            if batch_export:
                try:
                    # 获取历史评审结果
                    results = [review_result]
                    if include_history and review_result.review_history:
                        for history_item in review_result.review_history:
                            historical_result = ReviewResult(
                                business_value_score=history_item["scores"][
                                    "business_value"
                                ],
                                smart_score=history_item["scores"]["smart"],
                                completeness_score=history_item["scores"][
                                    "completeness"
                                ],
                                consistency_score=history_item["scores"]["consistency"],
                                clarity_score=history_item["scores"]["clarity"],
                                testability_score=history_item["scores"]["testability"],
                                blocking_issues=history_item.get("blocking_issues", []),
                                suggestions=history_item.get("suggestions", []),
                                review_timestamp=datetime.fromisoformat(
                                    history_item["timestamp"]
                                ),
                                review_history=[],
                            )
                            results.append(historical_result)

                    # 批量导出报告
                    exported_files = self.requirements_reviewer.batch_export(
                        results=results,
                        formats=[export_format],
                        output_dir=output_dir,
                        include_summary=True,
                    )

                    # 生成导出结果报告
                    report = f"""# 需求分析报告

## 本次评审结果
{self.requirements_reviewer.export_report(review_result, format=export_format)}

## 批量导出结果
已导出以下文件：
{chr(10).join([f"- {filepath}" for filepath in exported_files[export_format]])}"""

                    return report

                except Exception as e:
                    return f"批量导出失败: {str(e)}"

            # 如果只需要导出当前报告
            report = self.requirements_reviewer.export_report(
                review_result, format=export_format
            )

            # 如果需要保存到文件系统
            if save_to_file:
                try:
                    filepath = self.requirements_reviewer.save_report(
                        review_result, format=export_format, output_dir=output_dir
                    )
                    report = f"{report}\n\n> 报告已保存至：{filepath}"
                except Exception as e:
                    report = f"{report}\n\n> 保存报告失败: {str(e)}"

            return report
        except Exception as e:
            return f"需求分析失败: {str(e)}"
