"""
工作流步骤定义

定义工作流中的单个执行步骤
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """工作流步骤定义"""

    name: str = Field(..., description="步骤名称")
    description: str = Field(default="", description="步骤描述")
    agent_type: str = Field(..., description="执行该步骤的智能体类型")
    required_inputs: List[str] = Field(
        default_factory=list, description="必需的输入参数"
    )
    optional_inputs: List[str] = Field(
        default_factory=list, description="可选的输入参数"
    )
    outputs: List[str] = Field(default_factory=list, description="输出参数")
    timeout: int = Field(default=300, description="步骤执行超时时间（秒）")
    retry_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_retries": 3,
            "retry_delay": 1,
            "max_retry_delay": 60,
            "retry_on_exceptions": ["TimeoutError", "ConnectionError"],
        },
        description="重试配置",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="步骤元数据")

    def validate_inputs(self, provided_inputs: Dict[str, Any]) -> List[str]:
        """
        验证提供的输入参数

        Args:
            provided_inputs: 提供的输入参数字典

        Returns:
            List[str]: 缺失的必需参数列表
        """
        missing_required = []
        for required in self.required_inputs:
            if required not in provided_inputs:
                missing_required.append(required)
        return missing_required

    def get_all_inputs(self) -> List[str]:
        """获取所有输入参数（必需的和可选的）"""
        return self.required_inputs + self.optional_inputs

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """将步骤定义转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "required_inputs": self.required_inputs,
            "optional_inputs": self.optional_inputs,
            "outputs": self.outputs,
            "timeout": self.timeout,
            "retry_config": self.retry_config,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """从字典创建步骤实例"""
        return cls(**data)
