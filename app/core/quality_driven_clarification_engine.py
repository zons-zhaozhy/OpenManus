"""
质量导向的澄清引擎
基于用户反馈重新设计：目标导向、逆向思维、质量为本

核心理念：
1. 目标导向：明确每次澄清要达到的具体目标
2. 逆向思维：从最终需求文档质量倒推需要澄清的内容
3. 质量为本：以需求完整性和质量为终止条件，而非轮次数量
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.llm import LLM
from app.logger import logger


class RequirementDimension(Enum):
    """需求维度枚举"""

    FUNCTIONAL = "功能需求"
    NON_FUNCTIONAL = "非功能需求"
    USER_ROLES = "用户角色"
    BUSINESS_RULES = "业务规则"
    CONSTRAINTS = "约束条件"
    ACCEPTANCE_CRITERIA = "验收标准"
    INTEGRATION = "集成需求"
    DATA_REQUIREMENTS = "数据需求"


@dataclass
class DimensionQuality:
    """维度质量评估"""

    dimension: RequirementDimension
    completeness: float  # 完整性 0-1
    clarity: float  # 清晰度 0-1
    specificity: float  # 具体性 0-1
    feasibility: float  # 可行性 0-1
    overall_score: float  # 综合评分 0-1
    missing_aspects: List[str]  # 缺失方面
    improvement_suggestions: List[str]  # 改进建议


@dataclass
class ClarificationGoal:
    """澄清目标"""

    dimension: RequirementDimension
    target_quality: float  # 目标质量分数
    key_questions: List[str]  # 关键问题
    priority: int  # 优先级 1-5
    estimated_effort: str  # 预估澄清难度


class QualityDrivenClarificationEngine:
    """质量导向的澄清引擎"""

    def __init__(self):
        self.llm = LLM()
        self.quality_threshold = 0.8  # 整体质量阈值
        self.dimension_threshold = 0.7  # 单维度质量阈值
        self.max_clarification_attempts = 10  # 防止无限循环的最大尝试次数

    async def analyze_requirement_quality(
        self, requirement_text: str, clarification_history: List[Dict] = None
    ) -> Dict[RequirementDimension, DimensionQuality]:
        """
        分析需求质量 - 逆向思维：从最终文档质量要求倒推
        """
        logger.info("🎯 开始质量导向的需求分析...")

        # 构建质量分析提示词
        analysis_prompt = self._build_quality_analysis_prompt(
            requirement_text, clarification_history
        )

        # 并行分析所有维度
        dimension_tasks = []
        for dimension in RequirementDimension:
            task = self._analyze_single_dimension(
                dimension, requirement_text, clarification_history
            )
            dimension_tasks.append(task)

        # 等待所有分析完成
        dimension_results = await asyncio.gather(*dimension_tasks)

        # 构建质量评估结果
        quality_assessment = {}
        for i, dimension in enumerate(RequirementDimension):
            quality_assessment[dimension] = dimension_results[i]

        # 记录质量评估日志
        overall_quality = self._calculate_overall_quality(quality_assessment)
        logger.info(f"📊 需求整体质量评分: {overall_quality:.2f}")

        return quality_assessment

    async def _analyze_single_dimension(
        self,
        dimension: RequirementDimension,
        requirement_text: str,
        clarification_history: List[Dict] = None,
    ) -> DimensionQuality:
        """分析单个需求维度的质量"""

        prompt = f"""作为需求分析专家，请评估以下需求在【{dimension.value}】维度的质量：

需求文本："{requirement_text}"

澄清历史：{clarification_history if clarification_history else "无"}

请从以下角度评估：
1. 完整性（0-1）：该维度信息是否完整？
2. 清晰度（0-1）：表述是否清晰明确？
3. 具体性（0-1）：是否具体可实施？
4. 可行性（0-1）：是否在技术和业务上可行？

还需要识别：
- 缺失的关键方面
- 具体的改进建议

返回JSON格式：
{{
    "completeness": 0.7,
    "clarity": 0.8,
    "specificity": 0.6,
    "feasibility": 0.9,
    "missing_aspects": ["具体的功能边界", "性能指标"],
    "improvement_suggestions": ["需要明确具体的功能范围", "应该提供量化的性能要求"]
}}"""

        try:
            response = await self.llm.ask(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                stream=False,
            )

            result = self._parse_json_response(response)

            # 计算综合评分
            overall_score = (
                result.get("completeness", 0) * 0.3
                + result.get("clarity", 0) * 0.25
                + result.get("specificity", 0) * 0.25
                + result.get("feasibility", 0) * 0.2
            )

            return DimensionQuality(
                dimension=dimension,
                completeness=result.get("completeness", 0),
                clarity=result.get("clarity", 0),
                specificity=result.get("specificity", 0),
                feasibility=result.get("feasibility", 0),
                overall_score=overall_score,
                missing_aspects=result.get("missing_aspects", []),
                improvement_suggestions=result.get("improvement_suggestions", []),
            )

        except Exception as e:
            logger.error(f"分析维度 {dimension.value} 质量失败: {e}")
            return DimensionQuality(
                dimension=dimension,
                completeness=0.5,
                clarity=0.5,
                specificity=0.5,
                feasibility=0.5,
                overall_score=0.5,
                missing_aspects=["分析失败"],
                improvement_suggestions=["需要重新分析该维度"],
            )

    def _calculate_overall_quality(
        self, quality_assessment: Dict[RequirementDimension, DimensionQuality]
    ) -> float:
        """计算整体质量评分"""
        if not quality_assessment:
            return 0.0

        # 加权计算（核心维度权重更高）
        weights = {
            RequirementDimension.FUNCTIONAL: 0.25,
            RequirementDimension.NON_FUNCTIONAL: 0.15,
            RequirementDimension.USER_ROLES: 0.15,
            RequirementDimension.BUSINESS_RULES: 0.1,
            RequirementDimension.CONSTRAINTS: 0.1,
            RequirementDimension.ACCEPTANCE_CRITERIA: 0.15,
            RequirementDimension.INTEGRATION: 0.05,
            RequirementDimension.DATA_REQUIREMENTS: 0.05,
        }

        weighted_score = 0.0
        for dimension, quality in quality_assessment.items():
            weight = weights.get(dimension, 0.1)
            weighted_score += quality.overall_score * weight

        return weighted_score

    async def generate_targeted_clarification_goals(
        self, quality_assessment: Dict[RequirementDimension, DimensionQuality]
    ) -> List[ClarificationGoal]:
        """
        目标导向：生成针对性的澄清目标
        优先处理质量最低、影响最大的维度
        """
        logger.info("🎯 生成目标导向的澄清计划...")

        clarification_goals = []

        # 按质量评分和重要性排序
        sorted_dimensions = self._prioritize_dimensions(quality_assessment)

        for dimension, quality in sorted_dimensions:
            # 只有质量低于阈值的维度才需要澄清
            if quality.overall_score < self.dimension_threshold:
                goal = await self._create_clarification_goal(dimension, quality)
                clarification_goals.append(goal)

        # 按优先级排序
        clarification_goals.sort(key=lambda x: x.priority, reverse=True)

        logger.info(f"📋 生成了 {len(clarification_goals)} 个澄清目标")
        return clarification_goals

    def _prioritize_dimensions(
        self, quality_assessment: Dict[RequirementDimension, DimensionQuality]
    ) -> List[Tuple[RequirementDimension, DimensionQuality]]:
        """维度优先级排序"""

        # 重要性权重
        importance_weights = {
            RequirementDimension.FUNCTIONAL: 5,
            RequirementDimension.USER_ROLES: 4,
            RequirementDimension.ACCEPTANCE_CRITERIA: 4,
            RequirementDimension.NON_FUNCTIONAL: 3,
            RequirementDimension.BUSINESS_RULES: 3,
            RequirementDimension.CONSTRAINTS: 2,
            RequirementDimension.DATA_REQUIREMENTS: 2,
            RequirementDimension.INTEGRATION: 1,
        }

        # 计算优先级分数（质量越低、重要性越高，优先级越高）
        priority_scores = []
        for dimension, quality in quality_assessment.items():
            importance = importance_weights.get(dimension, 1)
            # 优先级 = 重要性 * (1 - 质量分数)
            priority_score = importance * (1 - quality.overall_score)
            priority_scores.append((priority_score, dimension, quality))

        # 按优先级分数降序排序
        priority_scores.sort(key=lambda x: x[0], reverse=True)

        return [(item[1], item[2]) for item in priority_scores]

    async def _create_clarification_goal(
        self, dimension: RequirementDimension, quality: DimensionQuality
    ) -> ClarificationGoal:
        """创建澄清目标"""

        # 基于缺失方面生成关键问题
        key_questions = await self._generate_targeted_questions(dimension, quality)

        # 计算优先级
        priority = self._calculate_priority(dimension, quality)

        # 估算澄清难度
        estimated_effort = self._estimate_clarification_effort(quality)

        return ClarificationGoal(
            dimension=dimension,
            target_quality=max(0.8, quality.overall_score + 0.3),  # 目标提升0.3分
            key_questions=key_questions,
            priority=priority,
            estimated_effort=estimated_effort,
        )

    async def _generate_targeted_questions(
        self, dimension: RequirementDimension, quality: DimensionQuality
    ) -> List[str]:
        """基于质量缺陷生成针对性问题"""

        prompt = f"""基于需求维度【{dimension.value}】的质量分析结果，生成3-5个最关键的澄清问题：

质量评估：
- 完整性: {quality.completeness:.2f}
- 清晰度: {quality.clarity:.2f}
- 具体性: {quality.specificity:.2f}
- 可行性: {quality.feasibility:.2f}

缺失方面：{quality.missing_aspects}
改进建议：{quality.improvement_suggestions}

请生成能够直接解决这些质量问题的具体问题，要求：
1. 问题要具体、有针对性
2. 能够直接获得可用的答案
3. 优先解决最严重的质量缺陷

返回JSON格式：
{{
    "questions": [
        "具体问题1",
        "具体问题2",
        "具体问题3"
    ]
}}"""

        try:
            response = await self.llm.ask(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                stream=False,
            )

            result = self._parse_json_response(response)
            return result.get(
                "questions", [f"请提供更多关于{dimension.value}的详细信息"]
            )

        except Exception as e:
            logger.error(f"生成 {dimension.value} 澄清问题失败: {e}")
            return [f"请详细描述{dimension.value}相关的具体要求"]

    def _calculate_priority(
        self, dimension: RequirementDimension, quality: DimensionQuality
    ) -> int:
        """计算澄清优先级"""

        # 基础优先级
        base_priority = {
            RequirementDimension.FUNCTIONAL: 5,
            RequirementDimension.USER_ROLES: 4,
            RequirementDimension.ACCEPTANCE_CRITERIA: 4,
            RequirementDimension.NON_FUNCTIONAL: 3,
            RequirementDimension.BUSINESS_RULES: 3,
            RequirementDimension.CONSTRAINTS: 2,
            RequirementDimension.DATA_REQUIREMENTS: 2,
            RequirementDimension.INTEGRATION: 1,
        }.get(dimension, 1)

        # 质量调整（质量越低，优先级越高）
        quality_adjustment = max(1, int((1 - quality.overall_score) * 3))

        return min(5, base_priority + quality_adjustment)

    def _estimate_clarification_effort(self, quality: DimensionQuality) -> str:
        """估算澄清难度"""
        avg_score = (quality.completeness + quality.clarity + quality.specificity) / 3

        if avg_score < 0.3:
            return "高难度"
        elif avg_score < 0.6:
            return "中难度"
        else:
            return "低难度"

    async def should_continue_clarification(
        self,
        current_quality_assessment: Dict[RequirementDimension, DimensionQuality],
        clarification_count: int = 0,
    ) -> Tuple[bool, str]:
        """
        质量为本：判断是否需要继续澄清
        """
        # 计算整体质量
        overall_quality = self._calculate_overall_quality(current_quality_assessment)

        # 防止无限循环
        if clarification_count >= self.max_clarification_attempts:
            return (
                False,
                f"已达到最大澄清次数({self.max_clarification_attempts})，当前质量: {overall_quality:.2f}",
            )

        # 整体质量达标检查
        if overall_quality >= self.quality_threshold:
            return (
                False,
                f"✅ 需求质量达标！整体评分: {overall_quality:.2f}/{self.quality_threshold}",
            )

        # 检查关键维度质量
        critical_dimensions = [
            RequirementDimension.FUNCTIONAL,
            RequirementDimension.USER_ROLES,
            RequirementDimension.ACCEPTANCE_CRITERIA,
        ]

        critical_quality_issues = []
        for dimension in critical_dimensions:
            quality = current_quality_assessment.get(dimension)
            if quality and quality.overall_score < self.dimension_threshold:
                critical_quality_issues.append(
                    f"{dimension.value}: {quality.overall_score:.2f}"
                )

        if critical_quality_issues:
            return (
                True,
                f"🔍 关键维度质量不达标，需要继续澄清: {', '.join(critical_quality_issues)}",
            )

        # 检查是否有维度质量过低
        low_quality_dimensions = []
        for dimension, quality in current_quality_assessment.items():
            if quality.overall_score < 0.5:  # 过低质量阈值
                low_quality_dimensions.append(
                    f"{dimension.value}: {quality.overall_score:.2f}"
                )

        if low_quality_dimensions:
            return (
                True,
                f"⚠️ 发现质量过低的维度，需要澄清: {', '.join(low_quality_dimensions)}",
            )

        return False, f"✅ 需求质量基本达标，整体评分: {overall_quality:.2f}"

    def generate_quality_report(
        self, quality_assessment: Dict[RequirementDimension, DimensionQuality]
    ) -> str:
        """生成质量评估报告"""

        overall_quality = self._calculate_overall_quality(quality_assessment)

        report = f"""
# 需求质量评估报告

## 📊 整体质量评分: {overall_quality:.2f}/1.0

## 📋 各维度详细评估:

"""

        for dimension, quality in quality_assessment.items():
            status = "✅" if quality.overall_score >= self.dimension_threshold else "⚠️"
            report += f"""
### {status} {dimension.value} (评分: {quality.overall_score:.2f})
- **完整性**: {quality.completeness:.2f}
- **清晰度**: {quality.clarity:.2f}
- **具体性**: {quality.specificity:.2f}
- **可行性**: {quality.feasibility:.2f}

**缺失方面**: {', '.join(quality.missing_aspects) if quality.missing_aspects else '无'}
**改进建议**: {', '.join(quality.improvement_suggestions) if quality.improvement_suggestions else '无'}
"""

        # 添加总体建议
        if overall_quality >= self.quality_threshold:
            report += "\n## 🎉 总体建议: 需求质量达标，可以进入下一阶段。"
        else:
            report += f"\n## 🔍 总体建议: 需求质量需要改进，建议重点关注评分低于{self.dimension_threshold}的维度。"

        return report

    def _build_quality_analysis_prompt(
        self, requirement_text: str, clarification_history: List[Dict] = None
    ) -> str:
        """构建质量分析提示词"""
        return f"""作为需求质量分析专家，请全面评估以下需求的质量状况：

需求描述: "{requirement_text}"

澄清历史: {clarification_history if clarification_history else "无"}

请从软件工程需求分析的角度，系统性评估需求在各个维度的质量水平。"""

    def _parse_json_response(self, response: str) -> Dict:
        """解析JSON响应"""
        import json
        import re

        try:
            # 尝试直接解析
            return json.loads(response)
        except:
            try:
                # 提取JSON部分
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {}
            except:
                logger.error(f"JSON解析失败: {response}")
                return {}

    def _calculate_goal_oriented_score(
        self, analysis_result: dict, clarification_history: List[dict]
    ) -> float:
        """
        计算目标导向评分 - 修正版
        评估是否有效达成最终目标：生成高质量需求规格说明书

        不再以轮次数量为指标，而是评估目标达成的有效性
        """
        goal_achievement_score = 0.0

        # 1. 最终目标完成度评估 (40%)
        final_quality = analysis_result.get("final_quality_score", 0.0)
        goal_completion = min(final_quality / 0.8, 1.0)  # 目标是达到0.8质量
        goal_achievement_score += goal_completion * 0.4

        # 2. 目标达成效率评估 (30%)
        # 评估达成目标的效率，而非单纯的轮次多少
        total_rounds = len(clarification_history)
        if total_rounds > 0:
            quality_improvement_per_round = final_quality / total_rounds
            efficiency_score = min(quality_improvement_per_round * 5, 1.0)  # 归一化
            goal_achievement_score += efficiency_score * 0.3

        # 3. 目标一致性评估 (20%)
        # 评估整个过程是否始终围绕最终目标进行
        consistency_score = self._evaluate_goal_consistency(clarification_history)
        goal_achievement_score += consistency_score * 0.2

        # 4. 目标价值实现评估 (10%)
        # 评估是否实现了用户的真实目标价值
        value_realization = self._evaluate_value_realization(analysis_result)
        goal_achievement_score += value_realization * 0.1

        return min(goal_achievement_score, 1.0)

    def _evaluate_goal_consistency(self, clarification_history: List[dict]) -> float:
        """评估目标一致性：整个过程是否始终围绕最终目标"""
        if not clarification_history:
            return 0.0

        consistency_indicators = []

        for record in clarification_history:
            questions = record.get("questions", [])
            # 评估问题是否都指向需求规格说明书的关键要素
            relevant_questions = 0
            total_questions = len(questions)

            for question in questions:
                question_text = question.get("question", "").lower()
                # 检查问题是否针对需求文档的核心要素
                core_elements = [
                    "功能需求",
                    "非功能需求",
                    "用户角色",
                    "业务规则",
                    "约束条件",
                    "验收标准",
                    "技术方案",
                    "实现方式",
                ]
                if any(element in question_text for element in core_elements):
                    relevant_questions += 1

            if total_questions > 0:
                consistency_indicators.append(relevant_questions / total_questions)

        return (
            sum(consistency_indicators) / len(consistency_indicators)
            if consistency_indicators
            else 0.0
        )

    def _evaluate_value_realization(self, analysis_result: dict) -> float:
        """评估价值实现：是否实现了用户的真实目标价值"""
        value_score = 0.0

        # 检查是否包含了需求文档的关键部分
        key_components = [
            "functional_requirements",  # 功能需求
            "non_functional_requirements",  # 非功能需求
            "user_stories",  # 用户故事
            "acceptance_criteria",  # 验收标准
            "technical_constraints",  # 技术约束
            "business_rules",  # 业务规则
        ]

        present_components = 0
        for component in key_components:
            if component in analysis_result:
                present_components += 1

        value_score = present_components / len(key_components)

        return value_score

    async def generate_clarification_questions(
        self, clarification_goals: List[ClarificationGoal]
    ) -> List[Dict[str, Any]]:
        """
        基于澄清目标生成具体的澄清问题
        """

        questions = []

        for goal in clarification_goals[:3]:  # 限制最多3个目标，避免过多问题
            for question_text in goal.key_questions[:2]:  # 每个目标最多2个问题
                question = {
                    "question": question_text,
                    "dimension": goal.dimension.value,
                    "priority": goal.priority,
                    "estimated_effort": goal.estimated_effort,
                    "target_quality": goal.target_quality,
                }
                questions.append(question)

        return questions
