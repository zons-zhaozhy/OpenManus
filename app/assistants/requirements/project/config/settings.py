"""
项目管理配置系统
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """存储配置"""

    type: str = Field(
        default="memory",
        description="存储类型：memory（内存）, sqlite（SQLite）, mysql（MySQL）等",
    )
    connection_string: Optional[str] = Field(
        default=None, description="数据库连接字符串"
    )
    table_prefix: str = Field(default="pm_", description="数据库表前缀")


class EventConfig(BaseModel):
    """事件配置"""

    enabled: bool = Field(default=True, description="是否启用事件系统")
    async_processing: bool = Field(default=False, description="是否异步处理事件")
    retry_count: int = Field(default=3, description="事件处理失败重试次数")


class RequirementStatusConfig(BaseModel):
    """需求状态配置"""

    name: str = Field(..., description="状态名称")
    description: str = Field(..., description="状态描述")
    color: str = Field(..., description="状态颜色")
    order: int = Field(..., description="状态顺序")
    is_final: bool = Field(default=False, description="是否为终态")
    allowed_transitions: List[str] = Field(
        default_factory=list, description="允许转换到的状态列表"
    )


class RequirementPriorityConfig(BaseModel):
    """需求优先级配置"""

    name: str = Field(..., description="优先级名称")
    description: str = Field(..., description="优先级描述")
    color: str = Field(..., description="优先级颜色")
    order: int = Field(..., description="优先级顺序")
    sla_hours: Optional[int] = Field(
        default=None, description="服务级别协议时间（小时）"
    )


class ProjectConfig(BaseModel):
    """项目配置"""

    storage: StorageConfig = Field(
        default_factory=StorageConfig, description="存储配置"
    )
    events: EventConfig = Field(default_factory=EventConfig, description="事件配置")
    statuses: Dict[str, RequirementStatusConfig] = Field(
        default_factory=lambda: {
            "new": RequirementStatusConfig(
                name="新建",
                description="新创建的需求",
                color="#808080",
                order=0,
                allowed_transitions=["in_progress"],
            ),
            "in_progress": RequirementStatusConfig(
                name="进行中",
                description="正在处理的需求",
                color="#FFA500",
                order=1,
                allowed_transitions=["review", "blocked"],
            ),
            "blocked": RequirementStatusConfig(
                name="阻塞",
                description="被阻塞的需求",
                color="#FF0000",
                order=2,
                allowed_transitions=["in_progress"],
            ),
            "review": RequirementStatusConfig(
                name="评审中",
                description="等待评审的需求",
                color="#00FF00",
                order=3,
                allowed_transitions=["done", "in_progress"],
            ),
            "done": RequirementStatusConfig(
                name="完成",
                description="已完成的需求",
                color="#0000FF",
                order=4,
                is_final=True,
                allowed_transitions=[],
            ),
        },
        description="需求状态配置",
    )
    priorities: Dict[str, RequirementPriorityConfig] = Field(
        default_factory=lambda: {
            "low": RequirementPriorityConfig(
                name="低",
                description="低优先级",
                color="#808080",
                order=0,
                sla_hours=72,
            ),
            "medium": RequirementPriorityConfig(
                name="中",
                description="中优先级",
                color="#FFA500",
                order=1,
                sla_hours=48,
            ),
            "high": RequirementPriorityConfig(
                name="高",
                description="高优先级",
                color="#FF0000",
                order=2,
                sla_hours=24,
            ),
        },
        description="需求优先级配置",
    )


# 默认配置实例
default_config = ProjectConfig()
