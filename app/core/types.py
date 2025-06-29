"""
类型定义
"""

from enum import Enum
from typing import Dict, List, Optional, Union

class AgentState(str, Enum):
    """代理状态"""
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    TERMINATED = "terminated"

class AgentRole(str, Enum):
    """代理角色"""
    CLARIFIER = "clarifier"
    ANALYST = "analyst"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"

class MessageType(str, Enum):
    """消息类型"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    ERROR = "error"

class Priority(int, Enum):
    """优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# 类型别名
AgentID = str
SessionID = str
MessageID = str
TaskID = str

# 复杂类型
Message = Dict[str, Union[str, Dict, List]]
Context = Dict[str, Union[str, int, float, bool, Dict, List]]
Metrics = Dict[str, Union[int, float]]
History = List[Dict[str, Union[str, Dict]]]
