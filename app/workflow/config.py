"""
工作流引擎配置
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    """工作流引擎配置"""

    # Redis配置
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis连接URL"
    )
    redis_prefix: str = Field(default="workflow:", description="Redis键前缀")
    redis_ttl: int = Field(default=86400, description="Redis键过期时间（秒）")

    # 工作流引擎配置
    max_concurrent_workflows: int = Field(default=10, description="最大并发工作流数")
    default_timeout: int = Field(default=300, description="默认步骤超时时间（秒）")
    max_retry_count: int = Field(default=3, description="最大重试次数")
    base_retry_delay: int = Field(default=1, description="基础重试延迟（秒）")
    max_retry_delay: int = Field(default=60, description="最大重试延迟（秒）")

    # 事件总线配置
    max_event_history: int = Field(default=1000, description="最大事件历史记录数")
    event_batch_size: int = Field(default=100, description="事件批处理大小")

    # 智能体配置
    agent_configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "requirement_clarifier": {
                "model": "deepseek",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            "business_analyst": {
                "model": "deepseek",
                "temperature": 0.5,
                "max_tokens": 2000,
            },
            "technical_analyst": {
                "model": "deepseek",
                "temperature": 0.3,
                "max_tokens": 2000,
            },
            "documentation_writer": {
                "model": "deepseek",
                "temperature": 0.3,
                "max_tokens": 4000,
            },
            "quality_reviewer": {
                "model": "deepseek",
                "temperature": 0.2,
                "max_tokens": 2000,
            },
        },
        description="智能体配置",
    )

    # 监控配置
    enable_monitoring: bool = Field(default=True, description="是否启用监控")
    metrics_interval: int = Field(default=60, description="指标收集间隔（秒）")

    class Config:
        arbitrary_types_allowed = True


# 默认配置实例
default_config = WorkflowConfig()
