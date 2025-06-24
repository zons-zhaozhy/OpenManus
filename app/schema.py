from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Message role options"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


ROLE_VALUES = tuple(role.value for role in Role)
ROLE_TYPE = Literal[ROLE_VALUES]  # type: ignore


class ToolChoice(str, Enum):
    """Tool choice options"""

    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"


TOOL_CHOICE_VALUES = tuple(choice.value for choice in ToolChoice)
TOOL_CHOICE_TYPE = Literal[TOOL_CHOICE_VALUES]  # type: ignore


class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    FINISHED = "finished"
    ERROR = "error"


class Function(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    """Represents a tool/function call in a message"""

    id: str
    type: str = "function"
    function: Function


class Message(BaseModel):
    """Represents a chat message in the conversation"""

    role: ROLE_TYPE = Field(...)  # type: ignore
    content: Optional[str] = Field(default=None)
    tool_calls: Optional[List[ToolCall]] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)

    def __add__(self, other) -> List["Message"]:
        """支持 Message + list 或 Message + Message 的操作"""
        if isinstance(other, list):
            return [self] + other
        elif isinstance(other, Message):
            return [self, other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )

    def __radd__(self, other) -> List["Message"]:
        """支持 list + Message 的操作"""
        if isinstance(other, list):
            return other + [self]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(other).__name__}' and '{type(self).__name__}'"
            )

    def to_dict(self) -> dict:
        """Convert message to dictionary format"""
        message = {"role": self.role}
        if self.content is not None:
            message["content"] = self.content
        if self.tool_calls is not None:
            message["tool_calls"] = [tool_call.dict() for tool_call in self.tool_calls]
        if self.name is not None:
            message["name"] = self.name
        if self.tool_call_id is not None:
            message["tool_call_id"] = self.tool_call_id
        if self.base64_image is not None:
            message["base64_image"] = self.base64_image
        return message

    @classmethod
    def user_message(
        cls, content: str, base64_image: Optional[str] = None
    ) -> "Message":
        """Create a user message"""
        return cls(role=Role.USER, content=content, base64_image=base64_image)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """Create a system message"""
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def assistant_message(
        cls, content: Optional[str] = None, base64_image: Optional[str] = None
    ) -> "Message":
        """Create an assistant message"""
        return cls(role=Role.ASSISTANT, content=content, base64_image=base64_image)

    @classmethod
    def tool_message(
        cls, content: str, name, tool_call_id: str, base64_image: Optional[str] = None
    ) -> "Message":
        """Create a tool message"""
        return cls(
            role=Role.TOOL,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            base64_image=base64_image,
        )

    @classmethod
    def from_tool_calls(
        cls,
        tool_calls: List[Any],
        content: Union[str, List[str]] = "",
        base64_image: Optional[str] = None,
        **kwargs,
    ):
        """Create ToolCallsMessage from raw tool calls.

        Args:
            tool_calls: Raw tool calls from LLM
            content: Optional message content
            base64_image: Optional base64 encoded image
        """
        formatted_calls = [
            {"id": call.id, "function": call.function.model_dump(), "type": "function"}
            for call in tool_calls
        ]
        return cls(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=formatted_calls,
            base64_image=base64_image,
            **kwargs,
        )


class Memory(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    max_messages: int = Field(default=100)

    def add_message(self, message: Message) -> None:
        """Add a message to memory"""
        self.messages.append(message)
        # Optional: Implement message limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def add_messages(self, messages: List[Message]) -> None:
        """Add multiple messages to memory"""
        self.messages.extend(messages)
        # Optional: Implement message limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()

    def get_recent_messages(self, n: int) -> List[Message]:
        """Get n most recent messages"""
        return self.messages[-n:]

    def get_messages(self) -> List[dict]:
        """Get messages in dict format for compatibility"""
        return [msg.to_dict() for msg in self.messages]

    def to_dict_list(self) -> List[dict]:
        """Convert messages to list of dicts"""
        return [msg.to_dict() for msg in self.messages]


# 项目制管理数据模型
class ProjectStatus(str, Enum):
    """项目状态"""

    PLANNING = "planning"  # 规划中
    ACTIVE = "active"  # 进行中
    ON_HOLD = "on_hold"  # 暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class ProjectStage(str, Enum):
    """项目阶段 - 一个项目的完整生命周期"""

    REQUIREMENTS_ANALYSIS = "requirements_analysis"  # 需求分析阶段
    SYSTEM_ARCHITECTURE = "system_architecture"  # 系统架构设计阶段
    DEVELOPMENT = "development"  # 开发实现阶段
    TESTING = "testing"  # 测试验证阶段
    DEPLOYMENT = "deployment"  # 部署上线阶段
    MAINTENANCE = "maintenance"  # 维护运营阶段


class ProjectType(str, Enum):
    """项目类型 - 按业务领域分类"""

    WEB_APPLICATION = "web_application"  # Web应用系统
    MOBILE_APPLICATION = "mobile_application"  # 移动应用
    DESKTOP_APPLICATION = "desktop_application"  # 桌面应用
    MANAGEMENT_SYSTEM = "management_system"  # 管理系统（如图书管理、库存管理）
    E_COMMERCE = "e_commerce"  # 电商系统
    CONTENT_MANAGEMENT = "content_management"  # 内容管理系统
    DATA_ANALYTICS = "data_analytics"  # 数据分析系统
    IOT_SYSTEM = "iot_system"  # 物联网系统
    AI_ML_SYSTEM = "ai_ml_system"  # 人工智能/机器学习系统
    ENTERPRISE_SOFTWARE = "enterprise_software"  # 企业软件
    GAME_APPLICATION = "game_application"  # 游戏应用
    OTHER = "other"  # 其他类型


class Project(BaseModel):
    """项目模型 - 所有助手工作的基础单元"""

    # 基础信息
    id: str = Field(..., description="项目唯一标识")
    name: str = Field(..., description="项目名称")
    description: str = Field(..., description="项目描述")

    # 项目目标和背景（核心指引信息）
    objective: str = Field(..., description="项目整体目标")
    background: str = Field(..., description="项目背景情况")
    success_criteria: List[str] = Field(default_factory=list, description="成功标准")
    constraints: List[str] = Field(default_factory=list, description="约束条件")

    # 项目管理信息
    type: ProjectType = Field(..., description="项目类型")
    status: ProjectStatus = Field(
        default=ProjectStatus.PLANNING, description="项目状态"
    )
    current_stage: ProjectStage = Field(
        default=ProjectStage.REQUIREMENTS_ANALYSIS, description="当前阶段"
    )
    priority: int = Field(default=3, description="优先级 1-5，5最高")

    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None

    # 项目上下文（为智能体提供指引）
    context: Dict[str, Any] = Field(default_factory=dict, description="项目上下文信息")
    stakeholders: List[str] = Field(default_factory=list, description="项目干系人")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="项目元数据")


class ProjectCodebase(BaseModel):
    """项目代码库 - 与项目一对一绑定"""

    id: str = Field(..., description="代码库唯一标识")
    project_id: str = Field(..., description="所属项目ID")

    # 代码库基础信息
    name: str = Field(..., description="代码库名称")
    description: str = Field(..., description="代码库描述")
    repository_url: Optional[str] = Field(None, description="代码仓库URL")
    local_path: str = Field(..., description="本地代码路径")

    # 技术信息
    main_language: str = Field(..., description="主要编程语言")
    framework: Optional[str] = Field(None, description="主要框架")
    dependencies: List[str] = Field(default_factory=list, description="主要依赖")

    # 代码分析信息
    total_files: int = Field(default=0, description="文件总数")
    code_files: int = Field(default=0, description="代码文件数")
    complexity_score: float = Field(default=0.0, description="复杂度评分")
    reusability_score: float = Field(default=0.0, description="可复用性评分")

    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_analyzed_at: Optional[datetime] = None

    # 分析结果缓存
    analysis_cache: Dict[str, Any] = Field(
        default_factory=dict, description="分析结果缓存"
    )


class KnowledgeBaseType(str, Enum):
    """知识库类型"""

    DOMAIN_KNOWLEDGE = "domain_knowledge"  # 领域知识
    TECHNICAL_PATTERNS = "technical_patterns"  # 技术模式
    BEST_PRACTICES = "best_practices"  # 最佳实践
    REQUIREMENTS_TEMPLATES = "requirements_templates"  # 需求模板
    ARCHITECTURE_PATTERNS = "architecture_patterns"  # 架构模式


class KnowledgeBase(BaseModel):
    """知识库模型 - 可挂载到多个项目"""

    id: str = Field(..., description="知识库唯一标识")
    name: str = Field(..., description="知识库名称")
    description: str = Field(..., description="知识库描述")
    type: KnowledgeBaseType = Field(..., description="知识库类型")

    # 知识库内容
    content: Dict[str, Any] = Field(default_factory=dict, description="知识库内容")
    patterns: List[Dict[str, Any]] = Field(default_factory=list, description="知识模式")
    templates: List[Dict[str, Any]] = Field(
        default_factory=list, description="模板集合"
    )

    # 版本信息
    version: str = Field(default="1.0.0", description="知识库版本")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 使用统计
    usage_count: int = Field(default=0, description="使用次数")
    project_mount_count: int = Field(default=0, description="项目挂载数")


class ProjectKnowledgeMount(BaseModel):
    """项目知识库挂载关系 - 多对多关系"""

    id: str = Field(..., description="挂载关系唯一标识")
    project_id: str = Field(..., description="项目ID")
    knowledge_base_id: str = Field(..., description="知识库ID")

    # 挂载配置
    mount_type: str = Field(
        default="read_only", description="挂载类型：read_only, read_write"
    )
    priority: int = Field(default=3, description="优先级 1-5，5最高")
    is_active: bool = Field(default=True, description="是否启用")

    # 挂载时间
    mounted_at: datetime = Field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None

    # 使用统计
    usage_count: int = Field(default=0, description="使用次数")

    # 挂载配置
    config: Dict[str, Any] = Field(default_factory=dict, description="挂载配置")


class ProjectContext(BaseModel):
    """项目上下文 - 为智能体提供项目指引"""

    project_id: str = Field(..., description="项目ID")

    # 核心指引信息
    objective_guidance: str = Field(..., description="目标指引")
    background_context: str = Field(..., description="背景上下文")
    success_criteria: List[str] = Field(default_factory=list, description="成功标准")
    constraints: List[str] = Field(default_factory=list, description="约束条件")

    # 当前阶段信息
    current_stage: str = Field(..., description="当前阶段")
    stage_objectives: List[str] = Field(default_factory=list, description="阶段目标")

    # 可用资源
    available_knowledge_bases: List[str] = Field(
        default_factory=list, description="可用知识库"
    )
    codebase_info: Optional[Dict[str, Any]] = Field(None, description="代码库信息")

    # 智能体协作信息
    active_agents: List[str] = Field(default_factory=list, description="活跃智能体")
    shared_memory: Dict[str, Any] = Field(default_factory=dict, description="共享记忆")

    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProjectSession(BaseModel):
    """项目会话 - 具体的工作会话"""

    id: str = Field(..., description="会话ID")
    project_id: str = Field(..., description="项目ID")

    # 会话信息
    name: str = Field(..., description="会话名称")
    description: str = Field(..., description="会话描述")
    session_type: str = Field(..., description="会话类型")

    # 会话状态
    status: str = Field(default="active", description="会话状态")
    current_agent: Optional[str] = Field(None, description="当前活跃智能体")

    # 会话数据
    context: Dict[str, Any] = Field(default_factory=dict, description="会话上下文")
    history: List[Dict[str, Any]] = Field(default_factory=list, description="会话历史")
    results: Dict[str, Any] = Field(default_factory=dict, description="会话结果")

    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# 需求分析相关模型
class RequirementAnalysisRequest(BaseModel):
    """需求分析请求模型"""

    content: str = Field(..., description="需求内容")
    domain: Optional[str] = Field(None, description="业务领域")
    priority: Optional[str] = Field(None, description="优先级")
    session_id: Optional[str] = Field(None, description="会话ID")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="上下文信息"
    )


class RequirementAnalysisResponse(BaseModel):
    """需求分析响应模型"""

    original_content: str = Field(..., description="原始需求内容")
    clarified_requirements: str = Field(..., description="澄清后的需求")
    technical_feasibility: Dict[str, Any] = Field(
        default_factory=dict, description="技术可行性评估"
    )
    recommendations: List[str] = Field(default_factory=list, description="建议清单")
    knowledge_insights: List[Dict[str, Any]] = Field(
        default_factory=list, description="知识库洞察"
    )
    code_insights: List[Dict[str, Any]] = Field(
        default_factory=list, description="代码库洞察"
    )
    confidence_score: float = Field(default=0.0, description="置信度评分")
    analysis_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="分析元数据"
    )

    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
