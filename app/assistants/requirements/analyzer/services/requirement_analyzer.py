"""
需求分析器服务实现
"""

import json
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.llm import LLM

from ...common.exceptions.requirement import RequirementAnalysisError
from ...common.models.requirement import Requirement
from ...storage.interfaces.storage import IRequirementStorage


class RequirementAnalysis(BaseModel):
    """需求分析结果"""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    requirement_points: List[str]
    requirement_type: str
    priority: str
    dependencies: List[str]
    acceptance_criteria: List[str]
    risk_points: List[str]


class ValidationResult(BaseModel):
    """需求验证结果"""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    is_valid: bool
    issues: List[str]
    suggestions: List[str]


class Suggestion(BaseModel):
    """需求改进建议"""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    aspect: str
    current_state: str
    suggested_change: str
    reason: str
    example: Optional[str]


class Conflict(BaseModel):
    """需求冲突"""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    type: str
    description: str
    severity: str
    affected_requirements: List[str]


class ConflictResult(BaseModel):
    """需求冲突检测结果"""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    has_conflicts: bool
    conflicts: List[Conflict]
    resolution_suggestions: List[str]


class RequirementAnalyzer:
    """需求分析器实现"""

    def __init__(
        self, requirement_storage: IRequirementStorage, llm: Optional[LLM] = None
    ):
        self._requirement_storage = requirement_storage
        self._llm = llm or LLM()

    async def analyze_requirement(self, text: str) -> RequirementAnalysis:
        """分析需求文本"""
        try:
            # 构建提示信息
            messages = [
                {
                    "role": "system",
                    "content": """你是一个专业的需求分析专家。请分析给定的需求文本，提取以下信息：
1. 核心需求点
2. 需求类型（功能性/非功能性）
3. 优先级（高/中/低）
4. 潜在的依赖关系
5. 验收标准
6. 风险点

请确保分析全面且准确。""",
                },
                {"role": "user", "content": text},
            ]

            # 调用LLM进行分析
            response = await self._llm.ask_tool(
                messages=messages,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "analyze_requirement",
                            "description": "Analyze the requirement text and extract key information",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "requirement_points": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of core requirement points",
                                    },
                                    "requirement_type": {
                                        "type": "string",
                                        "enum": ["functional", "non_functional"],
                                        "description": "Type of the requirement",
                                    },
                                    "priority": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"],
                                        "description": "Priority level of the requirement",
                                    },
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of potential dependencies",
                                    },
                                    "acceptance_criteria": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of acceptance criteria",
                                    },
                                    "risk_points": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of identified risk points",
                                    },
                                },
                                "required": [
                                    "requirement_points",
                                    "requirement_type",
                                    "priority",
                                    "dependencies",
                                    "acceptance_criteria",
                                    "risk_points",
                                ],
                            },
                        },
                    }
                ],
                tool_choice={
                    "type": "function",
                    "function": {"name": "analyze_requirement"},
                },
            )

            if not response or not response.tool_calls:
                raise RequirementAnalysisError(
                    "Failed to analyze requirement: No response from LLM"
                )

            # 解析响应
            result = response.tool_calls[0].function.arguments
            return RequirementAnalysis.parse_raw(result)

        except Exception as e:
            raise RequirementAnalysisError(f"Failed to analyze requirement: {str(e)}")

    async def validate_requirement(
        self, requirement: "Requirement"
    ) -> ValidationResult:
        """验证需求的完整性和一致性"""
        try:
            # 构建提示信息
            messages = [
                {
                    "role": "system",
                    "content": """你是一个专业的需求验证专家。请验证给定需求的完整性和一致性，检查：
1. 需求描述的清晰度
2. 验收标准的可测试性
3. 依赖关系的合理性
4. 潜在的问题和风险

请提供详细的分析结果和改进建议。""",
                },
                {
                    "role": "user",
                    "content": f"需求ID: {requirement.id}\n描述: {requirement.description}\n优先级: {requirement.priority}\n状态: {requirement.status}\n依赖: {', '.join(requirement.dependencies)}",
                },
            ]

            # 调用LLM进行验证
            response = await self._llm.ask_tool(
                messages=messages,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "validate_requirement",
                            "description": "Validate the requirement and provide feedback",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "is_valid": {
                                        "type": "boolean",
                                        "description": "Whether the requirement is valid",
                                    },
                                    "issues": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of identified issues",
                                    },
                                    "suggestions": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of improvement suggestions",
                                    },
                                },
                                "required": ["is_valid", "issues", "suggestions"],
                            },
                        },
                    }
                ],
                tool_choice={
                    "type": "function",
                    "function": {"name": "validate_requirement"},
                },
            )

            if not response or not response.tool_calls:
                raise RequirementAnalysisError(
                    "Failed to validate requirement: No response from LLM"
                )

            # 解析响应
            result = response.tool_calls[0].function.arguments
            return ValidationResult.parse_raw(result)

        except Exception as e:
            raise RequirementAnalysisError(f"Failed to validate requirement: {str(e)}")

    async def suggest_improvements(
        self, requirement: "Requirement"
    ) -> List[Suggestion]:
        """生成需求改进建议"""
        try:
            # 构建提示信息
            messages = [
                {
                    "role": "system",
                    "content": """你是一个专业的需求改进专家。请分析给定的需求，并提供具体的改进建议，包括：
1. 需要改进的方面
2. 当前状态
3. 建议的改变
4. 改进原因
5. 具体示例

请确保建议具体且可操作。""",
                },
                {
                    "role": "user",
                    "content": f"需求ID: {requirement.id}\n描述: {requirement.description}\n优先级: {requirement.priority}\n状态: {requirement.status}\n依赖: {', '.join(requirement.dependencies)}",
                },
            ]

            # 调用LLM生成建议
            response = await self._llm.ask_tool(
                messages=messages,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "suggest_improvements",
                            "description": "Generate improvement suggestions for the requirement",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "suggestions": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "aspect": {
                                                    "type": "string",
                                                    "description": "The aspect that needs improvement",
                                                },
                                                "current_state": {
                                                    "type": "string",
                                                    "description": "Current state of the aspect",
                                                },
                                                "suggested_change": {
                                                    "type": "string",
                                                    "description": "Suggested change",
                                                },
                                                "reason": {
                                                    "type": "string",
                                                    "description": "Reason for the suggestion",
                                                },
                                                "example": {
                                                    "type": "string",
                                                    "description": "Example of the improvement",
                                                },
                                            },
                                            "required": [
                                                "aspect",
                                                "current_state",
                                                "suggested_change",
                                                "reason",
                                            ],
                                        },
                                    }
                                },
                                "required": ["suggestions"],
                            },
                        },
                    }
                ],
                tool_choice={
                    "type": "function",
                    "function": {"name": "suggest_improvements"},
                },
            )

            if not response or not response.tool_calls:
                raise RequirementAnalysisError(
                    "Failed to generate suggestions: No response from LLM"
                )

            # 解析响应
            result = response.tool_calls[0].function.arguments
            suggestions_data = eval(result)
            return [
                Suggestion(**suggestion)
                for suggestion in suggestions_data["suggestions"]
            ]

        except Exception as e:
            raise RequirementAnalysisError(f"Failed to generate suggestions: {str(e)}")

    async def detect_conflicts(
        self, requirement: "Requirement", existing_requirements: List["Requirement"]
    ) -> ConflictResult:
        """检测需求之间的潜在冲突

        Args:
            requirement: 待检测的需求
            existing_requirements: 现有的需求列表

        Returns:
            ConflictResult: 冲突检测结果
        """
        try:
            # 构建提示信息
            messages = [
                {
                    "role": "system",
                    "content": """你是一个专业的需求分析专家。请分析给定的需求是否与现有需求存在冲突。
需要考虑以下方面：
1. 功能重叠或矛盾
2. 资源竞争
3. 技术约束冲突
4. 业务规则冲突
5. 性能影响

请提供详细的分析结果和解决建议。""",
                },
                {
                    "role": "user",
                    "content": f"""
新需求:
ID: {requirement.id}
描述: {requirement.description}
优先级: {requirement.priority}
状态: {requirement.status}
依赖: {', '.join(requirement.dependencies)}

现有需求:
{chr(10).join([f'ID: {r.id}{chr(10)}描述: {r.description}{chr(10)}优先级: {r.priority}{chr(10)}状态: {r.status}{chr(10)}依赖: {", ".join(r.dependencies)}{chr(10)}' for r in existing_requirements])}
""",
                },
            ]

            # 调用LLM进行冲突检测
            response = await self._llm.ask_tool(
                messages=messages,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "detect_conflicts",
                            "description": "Detect conflicts between requirements",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "has_conflicts": {
                                        "type": "boolean",
                                        "description": "Whether conflicts exist",
                                    },
                                    "conflicts": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {
                                                    "type": "string",
                                                    "description": "Type of conflict",
                                                },
                                                "description": {
                                                    "type": "string",
                                                    "description": "Description of the conflict",
                                                },
                                                "severity": {
                                                    "type": "string",
                                                    "enum": ["high", "medium", "low"],
                                                    "description": "Severity of the conflict",
                                                },
                                                "affected_requirements": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "description": "IDs of affected requirements",
                                                },
                                            },
                                            "required": [
                                                "type",
                                                "description",
                                                "severity",
                                                "affected_requirements",
                                            ],
                                        },
                                        "description": "List of identified conflicts",
                                    },
                                    "resolution_suggestions": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of conflict resolution suggestions",
                                    },
                                },
                                "required": [
                                    "has_conflicts",
                                    "conflicts",
                                    "resolution_suggestions",
                                ],
                            },
                        },
                    }
                ],
                tool_choice={
                    "type": "function",
                    "function": {"name": "detect_conflicts"},
                },
            )

            if not response or not response.tool_calls:
                raise RequirementAnalysisError(
                    "Failed to detect conflicts: No response from LLM"
                )

            # 解析响应
            result = response.tool_calls[0].function.arguments
            return ConflictResult.model_validate_json(result)

        except Exception as e:
            raise RequirementAnalysisError(f"Failed to detect conflicts: {str(e)}")
