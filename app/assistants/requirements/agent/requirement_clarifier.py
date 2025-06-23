"""
需求澄清智能体

负责通过智能对话澄清用户的模糊需求，提出关键问题，
引导用户明确表达需求的核心要素。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.agent.base import BaseAgent
from app.schema import Message

from ..schema.requirement_models import ClarificationQuestion, RequirementContext


@dataclass
class ClarificationSession:
    """澄清会话数据结构"""

    session_id: str
    user_input: str
    context: RequirementContext
    questions: List[ClarificationQuestion]
    answers: Dict[str, str]
    clarity_score: float = 0.0


class RequirementClarifier(BaseAgent):
    """需求澄清智能体"""

    def __init__(self):
        super().__init__(name="RequirementClarifier")
        self.clarification_sessions: Dict[str, ClarificationSession] = {}

    async def clarify_requirement(
        self, user_input: str, session_id: str = None
    ) -> ClarificationSession:
        """
        澄清用户需求

        Args:
            user_input: 用户输入的原始需求
            session_id: 会话ID，可选

        Returns:
            ClarificationSession: 澄清会话对象
        """
        if session_id and session_id in self.clarification_sessions:
            session = self.clarification_sessions[session_id]
        else:
            session_id = self._generate_session_id()
            session = ClarificationSession(
                session_id=session_id,
                user_input=user_input,
                context=self._analyze_context(user_input),
                questions=[],
                answers={},
            )
            self.clarification_sessions[session_id] = session

        # 生成澄清问题
        questions = await self._generate_clarification_questions(session)
        session.questions.extend(questions)

        # 计算清晰度得分
        session.clarity_score = self._calculate_clarity_score(session)

        return session

    async def answer_question(
        self, session_id: str, question_id: str, answer: str
    ) -> ClarificationSession:
        """
        回答澄清问题

        Args:
            session_id: 会话ID
            question_id: 问题ID
            answer: 用户答案

        Returns:
            ClarificationSession: 更新后的会话对象
        """
        if session_id not in self.clarification_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.clarification_sessions[session_id]
        session.answers[question_id] = answer

        # 重新评估清晰度
        session.clarity_score = self._calculate_clarity_score(session)

        # 如果还需要进一步澄清，生成新问题
        if session.clarity_score < 0.8:
            new_questions = await self._generate_follow_up_questions(session)
            session.questions.extend(new_questions)

        return session

    def _analyze_context(self, user_input: str) -> RequirementContext:
        """分析需求上下文"""
        # TODO: 实现需求上下文分析逻辑
        return RequirementContext(
            domain="未知", stakeholders=[], constraints=[], assumptions=[]
        )

    async def _generate_clarification_questions(
        self, session: ClarificationSession
    ) -> List[ClarificationQuestion]:
        """生成澄清问题"""
        # TODO: 基于LLM生成澄清问题
        questions = []

        # 基础问题模板
        base_questions = [
            "请详细描述您希望解决的具体问题是什么？",
            "这个系统的主要用户群体是谁？",
            "您期望的项目预算和时间范围是怎样的？",
            "有哪些必须满足的技术约束或业务规则？",
        ]

        for i, question_text in enumerate(base_questions):
            questions.append(
                ClarificationQuestion(
                    id=f"q_{i+1}",
                    text=question_text,
                    category="基础信息",
                    priority="high",
                )
            )

        return questions

    async def _generate_follow_up_questions(
        self, session: ClarificationSession
    ) -> List[ClarificationQuestion]:
        """生成后续澄清问题"""
        # TODO: 基于已有答案生成针对性问题
        return []

    def _calculate_clarity_score(self, session: ClarificationSession) -> float:
        """计算需求清晰度得分"""
        if not session.questions:
            return 0.0

        answered_count = len(session.answers)
        total_count = len(session.questions)

        # 基础得分基于回答率
        base_score = answered_count / total_count

        # TODO: 增加答案质量评分逻辑

        return min(base_score, 1.0)

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        import uuid

        return str(uuid.uuid4())

    def is_clarification_complete(self, session_id: str) -> bool:
        """判断澄清是否完成"""
        if session_id not in self.clarification_sessions:
            return False

        session = self.clarification_sessions[session_id]
        return session.clarity_score >= 0.8

    def get_clarified_requirement(self, session_id: str) -> Optional[str]:
        """获取澄清后的需求描述"""
        if not self.is_clarification_complete(session_id):
            return None

        session = self.clarification_sessions[session_id]

        # TODO: 基于原始输入和澄清答案生成完整需求描述
        clarified_text = f"原始需求：{session.user_input}\n\n"
        clarified_text += "澄清信息：\n"

        for question in session.questions:
            if question.id in session.answers:
                clarified_text += f"- {question.text}: {session.answers[question.id]}\n"

        return clarified_text
