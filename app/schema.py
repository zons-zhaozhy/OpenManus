from enum import Enum
from typing import Any, List, Literal, Optional, Union

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


class AgentState(str, Enum):
    """Agent execution states"""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


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

    def __add__(self, other) -> list:
        """支持 Message + list 或 Message + Message 的操作"""
        if isinstance(other, list):
            return [self] + other
        elif isinstance(other, Message):
            return [self, other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )

    def __radd__(self, other) -> list:
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
            ToolCall(id=call.id, function=Function(**call.function.model_dump()))
            for call in tool_calls
        ]
        content_str = (
            content
            if isinstance(content, str)
            else "\n".join(content) if isinstance(content, list) else ""
        )
        return cls(
            role=Role.ASSISTANT,
            content=content_str,
            tool_calls=formatted_calls if formatted_calls else None,
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

    def to_dict_list(self) -> List[dict]:
        """Convert messages to list of dicts"""
        return [msg.to_dict() for msg in self.messages]


class EventType(str, Enum):
    """Event types for WebSocket communication"""

    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    STAGE_CHANGE = "stage_change"
    LOG = "log"
    ERROR = "error"


class Event(BaseModel):
    """Event model for WebSocket communication"""

    type: EventType
    data: Any


class QuestionType(str, Enum):
    """问题类型枚举"""

    CHOICE = "choice"  # 单选题
    MULTI_CHOICE = "multi"  # 多选题
    YES_NO = "yes_no"  # 是/否问题
    SCALE = "scale"  # 量表问题（1-5分）
    SHORT_TEXT = "short_text"  # 简短文本
    CONFIRM = "confirm"  # 确认默认值


class Question(BaseModel):
    """问题基类"""

    type: QuestionType
    question: str
    description: Optional[str] = None
    required: bool = True


class ChoiceQuestion(Question):
    """选择题"""

    type: QuestionType = QuestionType.CHOICE
    options: List[str]
    default: Optional[int] = None  # 默认选项的索引


class MultiChoiceQuestion(Question):
    """多选题"""

    type: QuestionType = QuestionType.MULTI_CHOICE
    options: List[str]
    defaults: Optional[List[int]] = None  # 默认选中的选项索引列表


class YesNoQuestion(Question):
    """是/否问题"""

    type: QuestionType = QuestionType.YES_NO
    default: Optional[bool] = None


class ScaleQuestion(Question):
    """量表问题"""

    type: QuestionType = QuestionType.SCALE
    min_value: int = 1
    max_value: int = 5
    labels: Optional[List[str]] = None  # 刻度说明
    default: Optional[int] = None


class ShortTextQuestion(Question):
    """简短文本问题"""

    type: QuestionType = QuestionType.SHORT_TEXT
    max_length: Optional[int] = None
    placeholder: Optional[str] = None
    default: Optional[str] = None


class ConfirmQuestion(Question):
    """确认问题"""

    type: QuestionType = QuestionType.CONFIRM
    default_value: str
    default: bool = True


QuestionUnion = Union[
    ChoiceQuestion,
    MultiChoiceQuestion,
    YesNoQuestion,
    ScaleQuestion,
    ShortTextQuestion,
    ConfirmQuestion,
]


class QuestionResponse(BaseModel):
    """问题回答"""

    question_type: QuestionType
    response: Union[str, int, bool, List[int], List[str]]
    raw_input: str
