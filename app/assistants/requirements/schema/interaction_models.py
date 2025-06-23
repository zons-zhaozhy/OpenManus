"""
用户交互模型 - 便利的澄清作答途径

基于用户反馈设计的多种交互方式：
- 选择题：快速选择
- 填空题：精确输入
- 评分题：量化评估
- 多选题：复合选择
- 优先级排序：相对重要性
"""

from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """问题类型枚举"""

    SINGLE_CHOICE = "single_choice"  # 单选题
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题
    TEXT_INPUT = "text_input"  # 文本输入
    RATING_SCALE = "rating_scale"  # 评分题
    PRIORITY_RANKING = "priority_ranking"  # 优先级排序
    YES_NO = "yes_no"  # 是非题
    FILL_BLANK = "fill_blank"  # 填空题


class QuestionOption(BaseModel):
    """问题选项"""

    id: str = Field(description="选项ID")
    text: str = Field(description="选项文本")
    description: Optional[str] = Field(default=None, description="选项说明")
    icon: Optional[str] = Field(default=None, description="选项图标")


class ClarificationQuestion(BaseModel):
    """澄清问题模型"""

    id: str = Field(description="问题唯一ID")
    type: QuestionType = Field(description="问题类型")
    title: str = Field(description="问题标题")
    description: Optional[str] = Field(default=None, description="问题描述")
    options: Optional[List[QuestionOption]] = Field(
        default=None, description="选项列表"
    )
    placeholder: Optional[str] = Field(default=None, description="输入提示")
    required: bool = Field(default=True, description="是否必答")
    priority: int = Field(default=1, description="优先级(1-5)")
    category: str = Field(description="问题分类")

    # 评分题特有字段
    min_value: Optional[int] = Field(default=None, description="最小值")
    max_value: Optional[int] = Field(default=None, description="最大值")
    min_label: Optional[str] = Field(default=None, description="最小值标签")
    max_label: Optional[str] = Field(default=None, description="最大值标签")


class UserAnswer(BaseModel):
    """用户答案模型"""

    question_id: str = Field(description="问题ID")
    answer_type: QuestionType = Field(description="答案类型")

    # 不同类型的答案值
    text_value: Optional[str] = Field(default=None, description="文本答案")
    choice_value: Optional[str] = Field(default=None, description="单选答案")
    multi_choice_values: Optional[List[str]] = Field(
        default=None, description="多选答案"
    )
    rating_value: Optional[int] = Field(default=None, description="评分答案")
    priority_values: Optional[List[str]] = Field(default=None, description="优先级排序")

    confidence: Optional[int] = Field(default=None, description="答案确信度(1-5)")
    note: Optional[str] = Field(default=None, description="补充说明")


class ClarificationSession(BaseModel):
    """澄清会话模型"""

    session_id: str = Field(description="会话ID")
    user_input: str = Field(description="用户原始输入")
    questions: List[ClarificationQuestion] = Field(description="澄清问题列表")
    answers: Dict[str, UserAnswer] = Field(default_factory=dict, description="用户答案")
    current_question_index: int = Field(default=0, description="当前问题索引")
    clarity_score: float = Field(default=0.0, description="澄清度得分")
    status: Literal["active", "completed", "paused"] = Field(
        default="active", description="会话状态"
    )

    def get_next_question(self) -> Optional[ClarificationQuestion]:
        """获取下一个未回答的问题"""
        unanswered = [q for q in self.questions if q.id not in self.answers]
        if unanswered:
            # 按优先级排序
            unanswered.sort(key=lambda x: x.priority, reverse=True)
            return unanswered[0]
        return None

    def get_completion_rate(self) -> float:
        """获取完成率"""
        if not self.questions:
            return 0.0
        return len(self.answers) / len(self.questions)

    def get_priority_questions(self) -> List[ClarificationQuestion]:
        """获取高优先级未回答问题"""
        unanswered = [q for q in self.questions if q.id not in self.answers]
        return [q for q in unanswered if q.priority >= 4]


class QuestionGenerator:
    """问题生成器 - 提供便利的澄清问题创建"""

    @staticmethod
    def create_choice_question(
        question_id: str,
        title: str,
        options: List[str],
        category: str,
        description: str = None,
        multiple: bool = False,
        priority: int = 3,
    ) -> ClarificationQuestion:
        """创建选择题"""
        question_options = [
            QuestionOption(id=f"opt_{i}", text=opt) for i, opt in enumerate(options)
        ]

        return ClarificationQuestion(
            id=question_id,
            type=(
                QuestionType.MULTIPLE_CHOICE if multiple else QuestionType.SINGLE_CHOICE
            ),
            title=title,
            description=description,
            options=question_options,
            category=category,
            priority=priority,
        )

    @staticmethod
    def create_rating_question(
        question_id: str,
        title: str,
        category: str,
        min_val: int = 1,
        max_val: int = 5,
        min_label: str = "不重要",
        max_label: str = "非常重要",
        description: str = None,
        priority: int = 3,
    ) -> ClarificationQuestion:
        """创建评分题"""
        return ClarificationQuestion(
            id=question_id,
            type=QuestionType.RATING_SCALE,
            title=title,
            description=description,
            category=category,
            priority=priority,
            min_value=min_val,
            max_value=max_val,
            min_label=min_label,
            max_label=max_label,
        )

    @staticmethod
    def create_text_question(
        question_id: str,
        title: str,
        category: str,
        placeholder: str = "请输入您的回答...",
        description: str = None,
        priority: int = 3,
    ) -> ClarificationQuestion:
        """创建文本输入题"""
        return ClarificationQuestion(
            id=question_id,
            type=QuestionType.TEXT_INPUT,
            title=title,
            description=description,
            placeholder=placeholder,
            category=category,
            priority=priority,
        )

    @staticmethod
    def create_yes_no_question(
        question_id: str,
        title: str,
        category: str,
        description: str = None,
        priority: int = 3,
    ) -> ClarificationQuestion:
        """创建是非题"""
        options = [
            QuestionOption(id="yes", text="是", icon="✅"),
            QuestionOption(id="no", text="否", icon="❌"),
        ]

        return ClarificationQuestion(
            id=question_id,
            type=QuestionType.YES_NO,
            title=title,
            description=description,
            options=options,
            category=category,
            priority=priority,
        )


# 预定义的常用问题模板
class RequirementQuestionTemplates:
    """需求分析常用问题模板"""

    @staticmethod
    def get_user_type_question() -> ClarificationQuestion:
        """用户类型问题"""
        return QuestionGenerator.create_choice_question(
            question_id="user_type",
            title="您的主要用户群体是？",
            options=[
                "个人用户（C端）",
                "企业用户（B端）",
                "内部员工",
                "合作伙伴",
                "混合用户群体",
            ],
            category="用户分析",
            description="明确主要服务对象有助于更好地理解需求",
            priority=5,
        )

    @staticmethod
    def get_urgency_question() -> ClarificationQuestion:
        """紧急程度问题"""
        return QuestionGenerator.create_rating_question(
            question_id="urgency",
            title="项目的紧急程度如何？",
            category="项目约束",
            min_val=1,
            max_val=5,
            min_label="不急",
            max_label="非常紧急",
            description="帮助我们理解项目时间压力",
            priority=4,
        )

    @staticmethod
    def get_budget_question() -> ClarificationQuestion:
        """预算问题"""
        return QuestionGenerator.create_choice_question(
            question_id="budget_range",
            title="项目预算范围大概是？",
            options=["10万以内", "10-50万", "50-100万", "100万以上", "预算待定"],
            category="项目约束",
            description="预算范围有助于制定合适的解决方案",
            priority=3,
        )

    @staticmethod
    def get_platform_question() -> ClarificationQuestion:
        """平台需求问题"""
        return QuestionGenerator.create_choice_question(
            question_id="target_platform",
            title="希望在哪些平台上运行？",
            options=[
                "网页版（Web）",
                "手机APP（iOS/Android）",
                "桌面软件（Windows/Mac）",
                "微信小程序",
                "多平台支持",
            ],
            category="技术要求",
            multiple=True,
            description="明确目标平台有助于技术选型",
            priority=4,
        )
