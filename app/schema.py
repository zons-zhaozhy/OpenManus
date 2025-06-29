"""
数据模型定义
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ROLE_TYPE(str, Enum):
    """角色类型枚举"""

    REQUIREMENT_CLARIFIER = "requirement_clarifier"  # 需求澄清者
    BUSINESS_ANALYST = "business_analyst"  # 业务分析师
    SYSTEM_ARCHITECT = "system_architect"  # 系统架构师
    DATABASE_DESIGNER = "database_designer"  # 数据库设计师
    TECH_SELECTOR = "tech_selector"  # 技术选择器
    ARCHITECTURE_REVIEWER = "architecture_reviewer"  # 架构审查师
    CODE_GENERATOR = "code_generator"  # 代码生成器
    CODE_REVIEWER = "code_reviewer"  # 代码审查师
    TESTER = "tester"  # 测试工程师
    DEPLOYER = "deployer"  # 部署工程师
    TECHNICAL_WRITER = "technical_writer" # 技术文档编写师


class TOOL_CHOICE_TYPE(str, Enum):
    """工具选择类型枚举"""

    AUTO = "auto"  # 自动选择工具
    NONE = "none"  # 不使用工具
    REQUIRED = "required"  # 必须使用工具
    CLARIFICATION = "clarification"  # 需求澄清
    ANALYSIS = "analysis"  # 需求分析
    MODELING = "modeling"  # 需求建模
    VALIDATION = "validation"  # 需求验证
    DOCUMENTATION = "documentation"  # 需求文档
    REVIEW = "review"  # 需求评审
    CUSTOM = "custom"  # 自定义工具


class AgentState(str, Enum):
    """智能体状态枚举"""

    IDLE = "idle"  # 空闲
    INITIALIZING = "initializing"  # 初始化中
    THINKING = "thinking"  # 思考中
    WORKING = "working"  # 工作中
    WAITING = "waiting"  # 等待中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败
    TERMINATED = "terminated"  # 终止
    FINISHED = "finished"  # 完成

    # 工作流状态
    CLARIFICATION = "clarification"  # 需求澄清
    ANALYSIS = "analysis"  # 需求分析
    MODELING = "modeling"  # 需求建模
    VALIDATION = "validation"  # 需求验证
    DOCUMENTATION = "documentation"  # 需求文档
    REVIEW = "review"  # 需求评审
    CUSTOM = "custom"  # 自定义工具


class AgentAction(BaseModel):
    """智能体动作模型"""

    action_type: str = Field(..., description="动作类型")
    tool_choice: Optional[TOOL_CHOICE_TYPE] = Field(
        default=None, description="工具选择"
    )
    input_data: Optional[Dict] = Field(default=None, description="输入数据")
    output_data: Optional[Dict] = Field(default=None, description="输出数据")
    status: str = Field(default="pending", description="动作状态")
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: Optional[Dict] = Field(default=None, description="元数据")
    timestamp: float = Field(..., description="时间戳")


class Memory(BaseModel):
    """智能体记忆模型"""

    key: str = Field(default="default_memory", description="记忆键")
    value: Union[str, Dict, List] = Field(default_factory=dict, description="记忆值")
    type: str = Field(default="general", description="记忆类型")
    timestamp: float = Field(default_factory=time.time, description="时间戳")
    metadata: Optional[Dict] = Field(default=None, description="元数据")
    importance: float = Field(default=0.0, description="重要性分数")
    expiry: Optional[float] = Field(default=None, description="过期时间")
    tags: List[str] = Field(default_factory=list, description="标签列表")

    # 消息存储
    messages: List[Dict] = Field(default_factory=list, description="消息列表")

    def add_message(self, message: Dict):
        """添加消息到记忆中"""
        self.messages.append(message)
        self.timestamp = time.time()

    def clear(self):
        """清除所有消息"""
        self.messages = []
        self.timestamp = time.time()


class HumanInputRequired(BaseModel):
    """需要人类输入的模型"""

    prompt: str = Field(..., description="提示信息")
    options: Optional[List[str]] = Field(default=None, description="可选选项")
    context: Optional[Dict] = Field(default=None, description="上下文信息")
    timeout: Optional[float] = Field(default=None, description="超时时间")
    metadata: Optional[Dict] = Field(default=None, description="元数据")


class AgentResponse(BaseModel):
    """智能体响应模型"""

    content: str = Field(..., description="响应内容")
    type: str = Field(..., description="响应类型")
    confidence: float = Field(default=1.0, description="置信度")
    metadata: Optional[Dict] = Field(default=None, description="元数据")
    requires_human_input: bool = Field(default=False, description="是否需要人类输入")
    human_input_details: Optional[HumanInputRequired] = Field(
        default=None, description="人类输入详情"
    )
    next_actions: Optional[List[str]] = Field(default=None, description="下一步动作")
    timestamp: float = Field(default_factory=time.time, description="时间戳")


class Message(BaseModel):
    """消息模型"""

    content: str = Field(..., description="消息内容")
    type: str = Field(..., description="消息类型")
    metadata: Optional[Dict] = Field(default=None, description="元数据")
    timestamp: float = Field(default_factory=time.time, description="时间戳")

    @classmethod
    def user_message(cls, content: str, base64_image: Optional[str] = None):
        """创建用户消息"""
        metadata = {"role": "user"}
        if base64_image:
            metadata["image"] = base64_image
        return cls(content=content, type="user", metadata=metadata)

    @classmethod
    def system_message(cls, content: str):
        """创建系统消息"""
        return cls(content=content, type="system", metadata={"role": "system"})

    @classmethod
    def assistant_message(cls, content: str, base64_image: Optional[str] = None):
        """创建助手消息"""
        metadata = {"role": "assistant"}
        if base64_image:
            metadata["image"] = base64_image
        return cls(content=content, type="assistant", metadata=metadata)

    @classmethod
    def tool_message(
        cls,
        content: str,
        tool_name: str = "",
        tool_call_id: str = "",
        base64_image: Optional[str] = None,
        **kwargs
    ):
        """创建工具消息"""
        metadata = {
            "role": "tool",
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            **kwargs,
        }
        if base64_image:
            metadata["image"] = base64_image
        return cls(content=content, type="tool", metadata=metadata)

    @classmethod
    def from_tool_calls(cls, content: str, tool_calls: List):
        """从工具调用创建消息"""
        return cls(
            content=content,
            type="assistant",
            metadata={"role": "assistant", "tool_calls": tool_calls},
        )


class ClarificationRequest(BaseModel):
    """澄清请求"""

    session_id: Optional[str] = Field(default=None, description="会话ID")
    requirement: str = Field(..., description="需求内容")
    context: Optional[Dict] = Field(default=None, description="上下文信息")


class ClarificationAnswerRequest(BaseModel):
    """澄清回答请求"""

    session_id: Optional[str] = Field(default=None, description="会话ID")
    requirement: str = Field(..., description="需求内容")
    context: Optional[Dict] = Field(default=None, description="上下文信息")
    question: str = Field(..., description="问题")
    answer: str = Field(..., description="回答")


class ClarificationResponse(BaseModel):
    """澄清响应"""

    questions: List[str] = Field(default_factory=list, description="澄清问题列表")
    status: str = Field(..., description="状态")
    context: Optional[Dict] = Field(default=None, description="上下文信息")
    error: Optional[str] = Field(default=None, description="错误信息")


class SessionStatus(BaseModel):
    """会话状态"""

    session_id: str = Field(..., description="会话ID")
    last_activity: str = Field(..., description="最后活动时间")
    is_complete: bool = Field(..., description="是否完成")
    questions_count: int = Field(..., description="问题数量")
    current_state: str = Field(..., description="当前状态")


class ToolCall(BaseModel):
    """工具调用模型"""

    id: str = Field(..., description="调用ID")
    function: Dict = Field(..., description="函数信息")
    tool_name: Optional[str] = Field(default=None, description="工具名称")
    tool_args: Optional[Dict] = Field(default=None, description="工具参数")
    tool_result: Optional[Any] = Field(default=None, description="工具结果")
    status: str = Field(default="pending", description="调用状态")
    error: Optional[str] = Field(default=None, description="错误信息")
    timestamp: float = Field(default_factory=time.time, description="时间戳")


class ToolChoice(str, Enum):
    """工具选择枚举"""

    AUTO = "auto"  # 自动选择工具
    NONE = "none"  # 不使用工具
    REQUIRED = "required"  # 必须使用工具


class ToolChoiceModel(BaseModel):
    """工具选择模型"""

    tool_type: TOOL_CHOICE_TYPE = Field(..., description="工具类型")
    tool_name: str = Field(..., description="工具名称")
    tool_description: Optional[str] = Field(default=None, description="工具描述")
    parameters: Optional[Dict] = Field(default=None, description="工具参数")
    priority: int = Field(default=0, description="优先级")
    metadata: Optional[Dict] = Field(default=None, description="元数据")


class ProjectContext(BaseModel):
    """项目上下文模型"""

    project_id: str = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    project_description: Optional[str] = Field(default=None, description="项目描述")
    project_type: Optional[str] = Field(default=None, description="项目类型")
    client_info: Optional[Dict] = Field(default=None, description="客户信息")
    team_info: Optional[Dict] = Field(default=None, description="团队信息")
    requirements: Optional[List[Dict]] = Field(default=None, description="需求列表")
    constraints: Optional[List[str]] = Field(default=None, description="约束条件")
    timeline: Optional[Dict] = Field(default=None, description="时间线")
    budget: Optional[Dict] = Field(default=None, description="预算")
    stakeholders: Optional[List[Dict]] = Field(default=None, description="利益相关者")
    documents: Optional[List[Dict]] = Field(default=None, description="文档列表")
    metadata: Optional[Dict] = Field(default=None, description="元数据")
    created_at: float = Field(default_factory=time.time, description="创建时间")
    updated_at: float = Field(default_factory=time.time, description="更新时间")


class RequirementAnalysisRequest(BaseModel):
    """需求分析请求模型"""

    requirement_text: str = Field(..., description="需求文本")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    project_context: Optional[ProjectContext] = Field(
        default=None, description="项目上下文"
    )
    analysis_type: Optional[str] = Field(
        default="comprehensive", description="分析类型"
    )
    priority: Optional[int] = Field(default=0, description="优先级")
    metadata: Optional[Dict] = Field(default=None, description="元数据")


class RequirementAnalysisResponse(BaseModel):
    """需求分析响应模型"""

    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")
    result: Optional[Dict] = Field(default=None, description="分析结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: Optional[Dict] = Field(default=None, description="元数据")
    timestamp: float = Field(default_factory=time.time, description="时间戳")
