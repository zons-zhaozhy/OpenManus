"""对话上下文管理"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.tool.requirements_reviewer import ReviewResult


class DialogueContext(BaseModel):
    """对话上下文"""

    history: List[Dict[str, Any]] = Field(default_factory=list)
    accumulated_requirements: Dict[str, List[str]] = Field(default_factory=dict)
    clarifications: Dict[str, str] = Field(default_factory=dict)
    review_history: List[ReviewResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        """添加对话消息"""
        self.history.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_requirement(self, category: str, requirement: str) -> None:
        """添加需求"""
        if category not in self.accumulated_requirements:
            self.accumulated_requirements[category] = []
        if requirement not in self.accumulated_requirements[category]:
            self.accumulated_requirements[category].append(requirement)

    def add_clarification(self, point: str, question: str) -> None:
        """添加澄清问题"""
        self.clarifications[point] = question

    def add_review_result(self, result: ReviewResult) -> None:
        """添加评审结果"""
        self.review_history.append(result)

    def get_point_details(self, point: str) -> List[str]:
        """获取某个点的详细信息"""
        return self.accumulated_requirements.get(point, [])

    def get_all_requirements(self) -> Dict[str, List[str]]:
        """获取所有需求"""
        return self.accumulated_requirements

    def get_clarification(self, point: str) -> Optional[str]:
        """获取某个点的澄清问题"""
        return self.clarifications.get(point)

    def get_latest_review(self) -> Optional[ReviewResult]:
        """获取最新的评审结果"""
        return self.review_history[-1] if self.review_history else None

    def get_review_history(self) -> List[ReviewResult]:
        """获取评审历史"""
        return self.review_history

    def clear(self) -> None:
        """清空上下文"""
        self.history.clear()
        self.accumulated_requirements.clear()
        self.clarifications.clear()
        self.review_history.clear()
        self.metadata.clear()

    def get_context_summary(self) -> Dict[str, Any]:
        """获取上下文摘要"""
        return {
            "message_count": len(self.history),
            "requirement_categories": list(self.accumulated_requirements.keys()),
            "clarification_points": list(self.clarifications.keys()),
            "review_count": len(self.review_history),
            "metadata": self.metadata,
        }

    def export_requirements(self) -> Dict[str, Any]:
        """导出需求数据"""
        latest_review = self.get_latest_review()
        return {
            "requirements": self.accumulated_requirements,
            "clarifications": self.clarifications,
            "latest_review": latest_review.dict() if latest_review else None,
            "metadata": self.metadata,
            "timestamp": datetime.now().isoformat(),
        }
