"""
澄清问题生成器
负责基于质量评估结果生成针对性的澄清问题
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from loguru import logger

from app.llm import LLM

from .quality_assessor import DimensionQuality, RequirementDimension


class MissingAspectPriority(Enum):
    """缺失方面优先级"""

    CRITICAL = "关键"  # 必须澄清，否则无法进行
    HIGH = "重要"  # 强烈建议澄清，影响核心功能
    MEDIUM = "一般"  # 建议澄清，影响用户体验
    LOW = "可选"  # 可以暂缓，属于优化项


class ImpactScope(Enum):
    """影响范围"""

    CORE_BUSINESS = "核心业务"  # 影响核心业务逻辑
    USER_EXPERIENCE = "用户体验"  # 影响用户使用体验
    SYSTEM_QUALITY = "系统质量"  # 影响系统质量属性
    MAINTENANCE = "维护性"  # 影响后期维护


class RiskLevel(Enum):
    """风险级别"""

    HIGH_RISK = "高风险"  # 可能导致项目失败
    MEDIUM_RISK = "中风险"  # 可能导致返工
    LOW_RISK = "低风险"  # 影响有限


@dataclass
class ClarificationGoal:
    """澄清目标"""

    dimension: RequirementDimension
    target_quality: float  # 目标质量分数
    key_questions: List[str]  # 关键问题
    priority: int  # 优先级 1-5
    estimated_effort: str  # 预估澄清难度


@dataclass
class MissingAspectClassification:
    """缺失方面分类"""

    aspect: str  # 缺失方面描述
    priority: MissingAspectPriority  # 优先级
    impact_scope: ImpactScope  # 影响范围
    risk_level: RiskLevel  # 风险级别
    business_impact: float  # 业务影响度 (0-1)
    clarification_effort: str  # 澄清难度 (简单/中等/复杂)
    suggested_questions: List[str]  # 建议澄清问题
    rationale: str  # 分级理由


class QuestionGenerator:
    """澄清问题生成器"""

    def __init__(self):
        self.llm = LLM()

    async def generate_targeted_clarification_goals(
        self,
        quality_assessment: Dict[RequirementDimension, DimensionQuality],
        requirement_text: str = "",
    ) -> List[ClarificationGoal]:
        """
        基于质量评估生成针对性的澄清目标
        """
        logger.info("🎯 生成针对性澄清目标...")

        goals = []

        # 找出质量最低的维度，优先澄清
        sorted_dimensions = sorted(
            quality_assessment.items(), key=lambda x: x[1].overall_score
        )

        for dimension, quality in sorted_dimensions[:3]:  # 只处理质量最低的3个维度
            if quality.overall_score < 0.7:  # 只对质量不足的维度生成澄清目标

                # 计算目标质量（当前质量 + 0.3，但不超过0.9）
                target_quality = min(quality.overall_score + 0.3, 0.9)

                # 生成关键问题
                key_questions = await self._generate_dimension_questions(
                    dimension, quality, requirement_text
                )

                # 计算优先级（质量越低优先级越高）
                priority = max(1, int((1 - quality.overall_score) * 5))

                # 估算澄清难度
                effort = self._estimate_clarification_effort(quality)

                goal = ClarificationGoal(
                    dimension=dimension,
                    target_quality=target_quality,
                    key_questions=key_questions,
                    priority=priority,
                    estimated_effort=effort,
                )

                goals.append(goal)

        # 按优先级排序
        goals.sort(key=lambda g: g.priority, reverse=True)

        logger.info(f"生成了 {len(goals)} 个澄清目标")
        return goals

    async def generate_clarification_questions(
        self, clarification_goals: List[ClarificationGoal]
    ) -> List[str]:
        """
        基于澄清目标生成具体的澄清问题
        """
        logger.info("📝 生成澄清问题...")

        all_questions = []

        for goal in clarification_goals[:2]:  # 限制同时处理的目标数量
            questions = goal.key_questions[:2]  # 每个目标最多2个问题
            all_questions.extend(questions)

        # 去重和优化
        unique_questions = list(dict.fromkeys(all_questions))  # 保持顺序的去重

        # 限制问题总数
        final_questions = unique_questions[:5]

        logger.info(f"生成了 {len(final_questions)} 个澄清问题")
        return final_questions

    async def _generate_dimension_questions(
        self,
        dimension: RequirementDimension,
        quality: DimensionQuality,
        requirement_text: str,
    ) -> List[str]:
        """
        为特定维度生成澄清问题
        """

        # 构建针对性提示
        prompt = f"""基于需求分析，为【{dimension.value}】维度生成澄清问题。

需求文本："{requirement_text}"

当前维度质量评估：
- 完整性：{quality.completeness:.2f}
- 清晰度：{quality.clarity:.2f}
- 具体性：{quality.specificity:.2f}
- 可行性：{quality.feasibility:.2f}

缺失方面：{quality.missing_aspects}
改进建议：{quality.improvement_suggestions}

请生成2-3个具体的澄清问题，要求：
1. 直接针对质量不足的方面
2. 问题具体、易于回答
3. 能够有效提升该维度质量

请只返回问题列表，每行一个问题，不要编号。
"""

        try:
            response = await self.llm.achat(prompt)

            # 解析问题列表
            questions = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and "?" in line:
                    # 清理问题格式
                    question = line.strip("- ").strip("• ").strip()
                    if question:
                        questions.append(question)

            return questions[:3]  # 最多返回3个问题

        except Exception as e:
            logger.error(f"生成 {dimension.value} 维度问题失败: {e}")
            # 返回通用问题
            return [f"请详细描述{dimension.value}相关的具体要求。"]

    def _estimate_clarification_effort(self, quality: DimensionQuality) -> str:
        """
        估算澄清难度
        """
        if quality.overall_score < 0.3:
            return "复杂"
        elif quality.overall_score < 0.6:
            return "中等"
        else:
            return "简单"

    async def classify_missing_aspects(
        self,
        requirement_text: str,
        quality_assessment: Dict[RequirementDimension, DimensionQuality],
    ) -> List[MissingAspectClassification]:
        """
        分类缺失方面，确定优先级和影响
        """
        logger.info("🏷️ 分类缺失方面...")

        classifications = []

        for dimension, quality in quality_assessment.items():
            for missing_item in quality.missing_aspects:
                classification = await self._analyze_missing_aspect_priority(
                    {
                        "aspect": missing_item,
                        "dimension": dimension.value,
                        "quality_score": quality.overall_score,
                    },
                    requirement_text,
                )
                classifications.append(classification)

        # 按业务影响度排序
        classifications.sort(key=lambda c: c.business_impact, reverse=True)

        return classifications[:10]  # 最多返回10个分类

    async def _analyze_missing_aspect_priority(
        self, missing_item: Dict, requirement_text: str
    ) -> MissingAspectClassification:
        """
        分析单个缺失方面的优先级
        """

        prompt = f"""分析缺失方面的优先级和影响：

需求文本："{requirement_text}"
缺失方面：{missing_item['aspect']}
所属维度：{missing_item['dimension']}
当前质量：{missing_item['quality_score']:.2f}

请评估：
1. 优先级：关键/重要/一般/可选
2. 影响范围：核心业务/用户体验/系统质量/维护性
3. 风险级别：高风险/中风险/低风险
4. 业务影响度：0.0-1.0
5. 澄清难度：简单/中等/复杂
6. 分级理由：简要说明

请返回JSON格式：
{{
    "priority": "关键|重要|一般|可选",
    "impact_scope": "核心业务|用户体验|系统质量|维护性",
    "risk_level": "高风险|中风险|低风险",
    "business_impact": 0.0-1.0,
    "clarification_effort": "简单|中等|复杂",
    "rationale": "分级理由"
}}
"""

        try:
            response = await self.llm.achat(prompt)
            analysis = self._parse_json_response(response)

            # 生成澄清问题
            suggested_questions = [
                f"关于{missing_item['aspect']}，能否提供更多详细信息？",
                f"在{missing_item['dimension']}方面，{missing_item['aspect']}的具体要求是什么？",
            ]

            return MissingAspectClassification(
                aspect=missing_item["aspect"],
                priority=MissingAspectPriority(analysis["priority"]),
                impact_scope=ImpactScope(analysis["impact_scope"]),
                risk_level=RiskLevel(analysis["risk_level"]),
                business_impact=analysis["business_impact"],
                clarification_effort=analysis["clarification_effort"],
                suggested_questions=suggested_questions,
                rationale=analysis["rationale"],
            )

        except Exception as e:
            logger.error(f"分析缺失方面优先级失败: {e}")
            # 返回默认分类
            return MissingAspectClassification(
                aspect=missing_item["aspect"],
                priority=MissingAspectPriority.MEDIUM,
                impact_scope=ImpactScope.USER_EXPERIENCE,
                risk_level=RiskLevel.MEDIUM_RISK,
                business_impact=0.5,
                clarification_effort="中等",
                suggested_questions=[f"请详细说明{missing_item['aspect']}的要求。"],
                rationale="默认中等优先级",
            )

    def _parse_json_response(self, response: str) -> Dict:
        """解析LLM的JSON响应"""
        try:
            import json

            return json.loads(response)
        except:
            # 返回默认值
            return {
                "priority": "一般",
                "impact_scope": "用户体验",
                "risk_level": "中风险",
                "business_impact": 0.5,
                "clarification_effort": "中等",
                "rationale": "解析失败，使用默认值",
            }
