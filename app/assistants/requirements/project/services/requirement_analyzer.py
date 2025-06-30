"""
需求分析器服务实现
"""

from typing import List, Optional

from pydantic import BaseModel

from app.llm import LLM

from ..interfaces.storage import IRequirementStorage
from ..models.base import Requirement
from ..utils.exceptions import RequirementAnalysisError
from ..interfaces.event_publisher import IEventPublisher


class RequirementAnalysis(BaseModel):
    """需求分析结果"""

    requirement_points: List[str]
    requirement_type: str
    priority: str
    dependencies: List[str]
    acceptance_criteria: List[str]
    risk_points: List[str]


class ValidationResult(BaseModel):
    """需求验证结果"""

    is_valid: bool
    issues: List[str]
    suggestions: List[str]


class Suggestion(BaseModel):
    """需求改进建议"""

    aspect: str
    current_state: str
    suggested_change: str
    reason: str
    example: Optional[str]


class RequirementAnalyzer:
    """需求分析器实现"""

    def __init__(
        self, requirement_storage: IRequirementStorage, llm: Optional[LLM] = None, event_publisher: Optional[IEventPublisher] = None
    ):
        self._requirement_storage = requirement_storage
        self._llm = llm or LLM()
        self._event_publisher = event_publisher

    async def analyze_requirement(self, text: str, session_id: Optional[str] = None) -> RequirementAnalysis:
        """分析需求文本"""
        try:
            if self._event_publisher and session_id:
                from app.assistants.requirements.project.services.websocket_event_publisher import WebSocketEventPublisher
                if isinstance(self._event_publisher, WebSocketEventPublisher):
                    await self._event_publisher.publish_custom_event(session_id, "task_start", {"task_name": "需求分析"})
                else:
                    print(f"Starting requirement analysis for session {session_id}")

            # 构建提示信息
            messages: List[dict] = [
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
                messages=messages,  # type: ignore
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
            analysis_result = RequirementAnalysis.parse_raw(result)

            if self._event_publisher and session_id:
                from app.assistants.requirements.project.services.websocket_event_publisher import WebSocketEventPublisher
                if isinstance(self._event_publisher, WebSocketEventPublisher):
                    await self._event_publisher.publish_custom_event(session_id, "task_result", {"result": analysis_result.model_dump()})
                else:
                    print(f"Analysis result for session {session_id}: {analysis_result}")

            return analysis_result

        except Exception as e:
            raise RequirementAnalysisError(f"Failed to analyze requirement: {str(e)}")

    async def validate_requirement(self, requirement: Requirement, session_id: Optional[str] = None) -> ValidationResult:
        """验证需求的完整性和一致性"""
        try:
            if self._event_publisher and session_id:
                from app.assistants.requirements.project.services.websocket_event_publisher import WebSocketEventPublisher
                if isinstance(self._event_publisher, WebSocketEventPublisher):
                    await self._event_publisher.publish_custom_event(session_id, "task_start", {"task_name": "需求验证"})
                else:
                    print(f"Starting requirement validation for session {session_id}")

            # 构建提示信息
            messages: List[dict] = [
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
                messages=messages,  # type: ignore
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
            validation_result = ValidationResult.parse_raw(result)

            if self._event_publisher and session_id:
                from app.assistants.requirements.project.services.websocket_event_publisher import WebSocketEventPublisher
                if isinstance(self._event_publisher, WebSocketEventPublisher):
                    await self._event_publisher.publish_custom_event(session_id, "task_result", {"result": validation_result.model_dump()})
                else:
                    print(f"Validation result for session {session_id}: {validation_result}")

            return validation_result

        except Exception as e:
            raise RequirementAnalysisError(f"Failed to validate requirement: {str(e)}")

    async def suggest_improvements(self, requirement: Requirement, session_id: Optional[str] = None) -> List[Suggestion]:
        """生成需求改进建议"""
        try:
            if self._event_publisher and session_id:
                from app.assistants.requirements.project.services.websocket_event_publisher import WebSocketEventPublisher
                if isinstance(self._event_publisher, WebSocketEventPublisher):
                    await self._event_publisher.publish_custom_event(session_id, "task_start", {"task_name": "需求改进建议"})
                else:
                    print(f"Starting requirement improvement suggestions for session {session_id}")

            # 构建提示信息
            messages: List[dict] = [
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
                messages=messages,  # type: ignore
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
            suggestions = [
                Suggestion(**suggestion)
                for suggestion in suggestions_data["suggestions"]
            ]

            if self._event_publisher and session_id:
                from app.assistants.requirements.project.services.websocket_event_publisher import WebSocketEventPublisher
                if isinstance(self._event_publisher, WebSocketEventPublisher):
                    await self._event_publisher.publish_custom_event(session_id, "task_result", {"result": [s.model_dump() for s in suggestions]})
                else:
                    print(f"Improvement suggestions for session {session_id}: {suggestions}")

            return suggestions

        except Exception as e:
            raise RequirementAnalysisError(f"Failed to generate suggestions: {str(e)}")
