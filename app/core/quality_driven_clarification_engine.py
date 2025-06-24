"""
质量导向的澄清引擎
基于用户反馈重新设计：目标导向、逆向思维、质量为本

核心理念：
1. 目标导向：明确每次澄清要达到的具体目标
2. 逆向思维：从最终需求文档质量倒推需要澄清的内容
3. 质量为本：以需求完整性和质量为终止条件，而非轮次数量
"""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.config import REQUIREMENT_QUALITY_CONFIG
from app.llm import LLM


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


class QualityDrivenClarificationEngine:
    """质量导向的澄清引擎"""

    def __init__(self):
        """
        初始化质量驱动澄清引擎
        使用配置化参数，避免硬编码
        """
        from app.llm import LLM

        self.llm = LLM()

        # 从配置加载参数
        self.config = REQUIREMENT_QUALITY_CONFIG

        # 质量阈值（基于需求工程最佳实践）
        self.quality_threshold = self.config["quality_thresholds"]["overall_threshold"]
        self.dimension_threshold = self.config["quality_thresholds"][
            "dimension_threshold"
        ]
        self.excellent_threshold = self.config["quality_thresholds"][
            "excellent_threshold"
        ]

        # 澄清轮次控制
        self.max_rounds = self.config["clarification_rounds"]["max_rounds"]
        self.min_rounds = self.config["clarification_rounds"]["min_rounds"]
        self.early_stop_threshold = self.config["clarification_rounds"][
            "early_stop_threshold"
        ]

        # 维度权重（基于软件工程理论）
        self.dimension_weights = self.config["dimension_weights"]

        # 评分严格度配置
        self.scoring_config = self.config["scoring_strictness"]

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

请从以下角度评估（务实标准，不要过于苛刻）：

1. 完整性（0-1）：
   - 0.7-1.0: 核心信息基本齐全
   - 0.5-0.7: 主要内容明确，部分细节待补充
   - 0.3-0.5: 基本概念清楚，缺少重要细节
   - 0.0-0.3: 信息严重不足

2. 清晰度（0-1）：
   - 0.7-1.0: 表述清晰易懂
   - 0.5-0.7: 大部分内容清楚
   - 0.3-0.5: 基本能理解，需要澄清
   - 0.0-0.3: 表述模糊难懂

3. 具体性（0-1）：
   - 0.7-1.0: 有具体的操作描述
   - 0.5-0.7: 有一定具体描述
   - 0.3-0.5: 偏概念化，缺少细节
   - 0.0-0.3: 过于抽象笼统

4. 可行性（0-1）：
   - 0.7-1.0: 明确可行
   - 0.5-0.7: 基本可行
   - 0.3-0.5: 有挑战但可能实现
   - 0.0-0.3: 存在明显技术难题

注意：正常的业务需求描述通常应该获得0.6-0.8的评分，只有特别详细的才能达到0.9+。

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

            # 计算综合评分 - 恢复严谨的评分算法
            completeness = result.get("completeness", 0.3)  # 默认值降低
            clarity = result.get("clarity", 0.3)
            specificity = result.get("specificity", 0.3)
            feasibility = result.get("feasibility", 0.3)

            # 使用配置化的权重
            weights = [
                self.scoring_config["completeness_weight"],
                self.scoring_config["clarity_weight"],
                self.scoring_config["specificity_weight"],
                self.scoring_config["feasibility_weight"],
            ]
            scores = [completeness, clarity, specificity, feasibility]

            # 基础评分：加权平均
            overall_score = sum(
                score * weight for score, weight in zip(scores, weights)
            )

            # 严格的奖励机制：只有在所有维度都达到较高水平时才给奖励
            bonus_threshold = self.scoring_config["bonus_threshold"]
            bonus_multiplier = self.scoring_config["bonus_multiplier"]

            if all(score >= bonus_threshold for score in scores):
                overall_score = min(overall_score * bonus_multiplier, 1.0)

            # 质量惩罚：如果有维度严重不足，整体评分应该受影响
            min_score = min(scores)
            if min_score < 0.4:  # 如果有维度评分过低
                overall_score = min(overall_score, min_score + 0.3)  # 限制总分

            # 确保评分在合理范围内
            overall_score = max(0.0, min(1.0, overall_score))

            return DimensionQuality(
                dimension=dimension,
                completeness=completeness,
                clarity=clarity,
                specificity=specificity,
                feasibility=feasibility,
                overall_score=overall_score,
                missing_aspects=result.get("missing_aspects", []),
                improvement_suggestions=result.get("improvement_suggestions", []),
            )

        except Exception as e:
            logger.error(f"分析维度 {dimension.value} 质量失败: {e}")
            # 尝试简化提示词重试一次
            try:
                logger.info(f"尝试简化提示词重新分析 {dimension.value}")
                simple_prompt = f"""请简单评估以下需求在【{dimension.value}】维度的质量（0-1分）：

需求文本："{requirement_text}"

返回JSON格式：
{{
    "completeness": 0.5,
    "clarity": 0.5,
    "specificity": 0.5,
    "feasibility": 0.5,
    "missing_aspects": ["需要补充的信息"],
    "improvement_suggestions": ["改进建议"]
}}"""

                response = await self.llm.ask(
                    messages=[{"role": "user", "content": simple_prompt}],
                    temperature=0.1,
                    stream=False,
                )

                result = self._parse_json_response(response)

                # 计算综合评分
                overall_score = (
                    result.get("completeness", 0.5) * 0.3
                    + result.get("clarity", 0.5) * 0.25
                    + result.get("specificity", 0.5) * 0.25
                    + result.get("feasibility", 0.5) * 0.2
                )

                return DimensionQuality(
                    dimension=dimension,
                    completeness=result.get("completeness", 0.5),
                    clarity=result.get("clarity", 0.5),
                    specificity=result.get("specificity", 0.5),
                    feasibility=result.get("feasibility", 0.5),
                    overall_score=overall_score,
                    missing_aspects=result.get(
                        "missing_aspects", ["分析异常，需要重新评估"]
                    ),
                    improvement_suggestions=result.get(
                        "improvement_suggestions", ["建议重新分析该维度"]
                    ),
                )

            except Exception as retry_error:
                logger.error(f"重试分析维度 {dimension.value} 仍然失败: {retry_error}")
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
        """
        计算整体质量评分

        优化权重分配：功能需求和用户角色权重更高
        """
        if not quality_assessment:
            return 0.0

        # 调整维度权重 - 让核心维度权重更高
        dimension_weights = {
            RequirementDimension.FUNCTIONAL: 0.25,  # 功能需求最重要
            RequirementDimension.USER_ROLES: 0.20,  # 用户角色很重要
            RequirementDimension.ACCEPTANCE_CRITERIA: 0.15,  # 验收标准重要
            RequirementDimension.NON_FUNCTIONAL: 0.12,  # 非功能需求
            RequirementDimension.BUSINESS_RULES: 0.10,  # 业务规则
            RequirementDimension.CONSTRAINTS: 0.08,  # 约束条件
            RequirementDimension.INTEGRATION: 0.05,  # 集成需求
            RequirementDimension.DATA_REQUIREMENTS: 0.05,  # 数据需求
        }

        weighted_scores = []
        total_weight = 0.0

        for dimension, quality in quality_assessment.items():
            weight = dimension_weights.get(dimension, 0.1)  # 默认权重0.1
            weighted_score = quality.overall_score * weight
            weighted_scores.append(weighted_score)
            total_weight += weight

        # 确保权重总和为1
        if total_weight > 0:
            overall_quality = sum(weighted_scores) / total_weight
        else:
            overall_quality = sum(
                q.overall_score for q in quality_assessment.values()
            ) / len(quality_assessment)

        return min(overall_quality, 1.0)  # 确保不超过1.0

    async def generate_targeted_clarification_goals(
        self, quality_assessment: Dict, requirement_text: str = ""
    ) -> List[str]:
        """
        基于质量评估生成有针对性的澄清目标

        新策略：使用分级处理机制，优先处理关键和重要的缺失方面
        """
        clarification_goals = []

        # 使用传入的需求文本，如果为空则使用默认值
        if not requirement_text:
            requirement_text = "待获取的需求文本"

        # 使用分级处理机制
        try:
            classified_aspects = await self.classify_missing_aspects(
                requirement_text, quality_assessment
            )

            # 按分级策略生成澄清目标
            processed_count = 0

            # 1. 首先处理关键(CRITICAL)缺失方面
            for classification in classified_aspects:
                if (
                    classification.priority == MissingAspectPriority.CRITICAL
                    and processed_count < 3
                ):  # 每轮最多3个关键问题
                    goal = f"🚨【关键-{classification.impact_scope.value}】{classification.aspect}"
                    clarification_goals.append(goal)
                    processed_count += 1

            # 2. 然后处理重要(HIGH)缺失方面
            for classification in classified_aspects:
                if (
                    classification.priority == MissingAspectPriority.HIGH
                    and processed_count < 5
                ):  # 总共最多5个问题
                    goal = f"🔴【重要-{classification.impact_scope.value}】{classification.aspect}"
                    clarification_goals.append(goal)
                    processed_count += 1

            # 3. 如果还有空间，处理一般(MEDIUM)缺失方面（仅限核心业务影响）
            for classification in classified_aspects:
                if (
                    classification.priority == MissingAspectPriority.MEDIUM
                    and classification.impact_scope == ImpactScope.CORE_BUSINESS
                    and processed_count < 5
                ):
                    goal = f"🟡【一般-核心业务】{classification.aspect}"
                    clarification_goals.append(goal)
                    processed_count += 1

        except Exception as e:
            logger.error(f"分级处理失败，使用降级策略: {e}")
            # 降级处理：直接从质量分析中提取
            for dimension_name, analysis in quality_assessment.items():
                if isinstance(analysis, dict) and "missing_aspects" in analysis:
                    missing_aspects = analysis["missing_aspects"]
                    if missing_aspects:
                        for aspect in missing_aspects[:2]:
                            goal = f"【{dimension_name}】{aspect}"
                            clarification_goals.append(goal)

        # 如果没有找到分级的缺失方面，生成默认目标
        if not clarification_goals:
            clarification_goals = [
                "🚨【关键-核心业务】明确系统的核心功能和操作流程",
                "🔴【重要-用户体验】定义用户角色和权限分配",
                "🟡【一般-系统质量】制定具体的性能指标和验收标准",
            ]

        return clarification_goals[:5]  # 最多5个目标

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
                # 安全提取问题文本
                if isinstance(question, dict):
                    question_text = question.get("question", "").lower()
                elif isinstance(question, str):
                    question_text = question.lower()
                else:
                    question_text = str(question).lower()

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
        self, clarification_goals: List[str]
    ) -> List[str]:
        """
        基于澄清目标生成精准的问题

        新策略：根据质量分析的"缺失方面"生成针对性问题
        """
        if not clarification_goals:
            return ["请提供更详细的需求说明，以便进行深入分析。"]

        # 构建智能提示词，针对缺失方面生成问题
        prompt = f"""作为专业的需求分析师，基于质量分析结果生成精准的澄清问题。

## 当前需要澄清的目标：
{chr(10).join([f"- {goal}" for goal in clarification_goals])}

## 要求：
1. 每个问题必须针对具体的缺失方面
2. 问题要具体、可操作、有明确的回答方向
3. 避免模糊笼统的问题
4. 优先关注功能需求、用户角色、验收标准等关键维度
5. 问题要引导用户提供量化、具体的信息

## 输出格式：
请直接输出3-4个澄清问题，每行一个问题。

示例格式：
1. 学生信息管理功能具体包含哪些操作？请列出增删改查的详细流程。
2. 系统需要支持多少并发用户？请提供具体的性能指标（如200用户同时登录）。
3. 请明确每个用户角色的具体权限，例如教师是否可以修改学生基本信息？
"""

        try:
            from app.llm import LLM
            from app.schema import Message

            llm = LLM()
            messages = [Message.user_message(prompt)]

            response = await llm.ask(
                messages=messages,
                temperature=0.3,
                stream=False,
            )

            # 解析问题
            questions = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line and len(line) > 10:  # 过滤太短的行
                    # 移除序号前缀
                    import re

                    line = re.sub(r"^\d+\.\s*", "", line)
                    line = re.sub(r"^[-*]\s*", "", line)
                    if line:
                        questions.append(line)

            # 确保至少有一个问题
            if not questions:
                questions = ["请提供更详细的需求信息，包括具体的功能要求和性能指标。"]

            return questions[:4]  # 最多4个问题

        except Exception as e:
            logger.error(f"生成澄清问题失败: {e}")
            # 降级处理
            return [
                "请详细描述系统的核心功能，包括具体的操作流程。",
                "请明确用户角色和权限分配的具体要求。",
                "请提供系统的性能指标要求，如并发用户数、响应时间等。",
            ]

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
        """解析JSON响应 - 增强容错性"""
        import json
        import re

        if not response or not response.strip():
            logger.warning("LLM返回空响应，使用默认值")
            return self._get_default_response()

        # 清理响应字符串
        cleaned_response = response.strip()

        try:
            # 尝试直接解析
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            try:
                # 移除markdown代码块标记
                if cleaned_response.startswith("```json"):
                    cleaned_response = (
                        cleaned_response.replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response.replace("```", "").strip()

                # 再次尝试解析
                return json.loads(cleaned_response)
            except json.JSONDecodeError:
                try:
                    # 尝试提取JSON部分
                    json_match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)
                    if json_match:
                        json_text = json_match.group()
                        return json.loads(json_text)
                    else:
                        logger.error(f"无法找到有效JSON: {cleaned_response[:200]}...")
                        return self._get_default_response()
                except json.JSONDecodeError as e:
                    logger.error(
                        f"JSON解析最终失败: {e}, 响应内容: {cleaned_response[:200]}..."
                    )
                    return self._get_default_response()

    def _get_default_response(self) -> Dict:
        """返回默认响应结构"""
        return {
            "completeness": 0.5,
            "clarity": 0.5,
            "specificity": 0.5,
            "feasibility": 0.5,
            "missing_aspects": ["分析响应异常"],
            "improvement_suggestions": ["需要重新分析"],
            "questions": ["请提供更多详细信息"],
        }

    async def should_continue_clarification(
        self, quality_analysis: Dict, current_round: int, requirement_text: str = ""
    ) -> tuple:
        """
        判断是否应该继续澄清

        基于科学的质量标准、设计就绪度和最少澄清轮次要求
        """
        overall_quality = self._calculate_overall_quality(quality_analysis)

        # 使用配置化的阈值
        overall_threshold = self.quality_threshold
        dimension_threshold = self.dimension_threshold
        max_rounds = self.max_rounds
        min_rounds = self.min_rounds
        design_threshold = self.config["quality_thresholds"][
            "design_readiness_threshold"
        ]

        # 1. 检查是否达到最大轮次
        if current_round >= max_rounds:
            return False, f"🔄 已达到最大澄清轮次({max_rounds}轮)"

        # 2. 检查是否满足最少澄清轮次要求
        if current_round < min_rounds:
            return (
                True,
                f"📝 需要完成最少{min_rounds}轮澄清以确保质量（当前第{current_round}轮）",
            )

        # 3. 检查整体质量
        if overall_quality < overall_threshold:
            return (
                True,
                f"📊 整体质量不达标: {overall_quality:.2f} < {overall_threshold}",
            )

        # 4. 检查各维度质量
        low_quality_dimensions = []
        for dim_name, analysis in quality_analysis.items():
            if isinstance(analysis, dict) and "score" in analysis:
                if analysis["score"] < dimension_threshold:
                    low_quality_dimensions.append(
                        f"{dim_name}: {analysis['score']:.2f}"
                    )

        if low_quality_dimensions:
            return True, f"🔍 关键维度质量不达标: {', '.join(low_quality_dimensions)}"

        # 5. 评估设计就绪度
        if requirement_text:
            try:
                design_readiness = await self.assess_design_readiness(
                    requirement_text, quality_analysis
                )
                readiness_score = design_readiness.get("overall_readiness", 0)

                if readiness_score < design_threshold:
                    blocking_issues = design_readiness.get("blocking_issues", [])
                    return (
                        True,
                        f"🎯 设计就绪度不足: {readiness_score:.2f} < {design_threshold}，阻塞问题: {', '.join(blocking_issues[:3])}",
                    )

                logger.info(
                    f"✅ 设计就绪度达标: {readiness_score:.2f} ({design_readiness.get('readiness_level', '未知')})"
                )
            except Exception as e:
                logger.warning(f"设计就绪度评估异常，继续澄清: {e}")
                return True, f"⚠️ 设计就绪度评估异常，建议继续澄清"

        # 6. 冲突分析 🔥 新增
        try:
            conflict_analysis = await self.analyze_knowledge_and_code_conflicts(
                requirement_text, quality_analysis
            )

            conflict_level = conflict_analysis.get("overall_conflict_level", "unknown")
            critical_conflicts = conflict_analysis.get("critical_conflicts", [])

            if conflict_level == "critical" and len(critical_conflicts) > 0:
                conflict_descriptions = [
                    c.get("description", "")[:50] for c in critical_conflicts[:2]
                ]
                return (
                    True,
                    f"⚠️ 发现严重冲突需要解决: {conflict_level}，冲突: {', '.join(conflict_descriptions)}",
                )

            if conflict_analysis.get("requires_stakeholder_decision", False):
                return (
                    True,
                    f"🤝 需要利益相关者决策: 发现{len(critical_conflicts)}个关键冲突",
                )

            logger.info(
                f"🔍 冲突分析完成: {conflict_level}级别，{len(critical_conflicts)}个严重冲突"
            )

        except Exception as e:
            logger.warning(f"冲突分析异常，但不阻塞流程: {e}")
            # 冲突分析异常不应该阻塞整个流程

        # 7. 所有条件满足，可以结束澄清
        return (
            False,
            f"✅ 需求质量达标且设计就绪，无严重冲突，整体评分: {overall_quality:.2f}",
        )

    async def classify_missing_aspects(
        self, requirement_text: str, quality_analysis: Dict
    ) -> List[MissingAspectClassification]:
        """
        智能分级处理需求缺失方面

        基于业务影响、风险级别、澄清难度等多维度进行分级
        """
        classifications = []

        # 收集所有维度的缺失方面
        all_missing_aspects = []
        for dim_name, analysis in quality_analysis.items():
            if isinstance(analysis, dict) and "missing_aspects" in analysis:
                for aspect in analysis["missing_aspects"]:
                    all_missing_aspects.append(
                        {
                            "dimension": dim_name,
                            "aspect": aspect,
                            "dimension_score": analysis.get("score", 0.5),
                        }
                    )

        # 对每个缺失方面进行智能分级
        for missing_item in all_missing_aspects:
            classification = await self._analyze_missing_aspect_priority(
                missing_item, requirement_text
            )
            classifications.append(classification)

        # 按优先级和业务影响排序
        classifications.sort(
            key=lambda x: (
                self._get_priority_weight(x.priority),
                x.business_impact,
                self._get_risk_weight(x.risk_level),
            ),
            reverse=True,
        )

        return classifications

    async def _analyze_missing_aspect_priority(
        self, missing_item: Dict, requirement_text: str
    ) -> MissingAspectClassification:
        """
        分析单个缺失方面的优先级和分类
        """
        dimension = missing_item["dimension"]
        aspect = missing_item["aspect"]

        # 构建智能分级提示词
        prompt = f"""作为需求分析专家，请对以下缺失方面进行专业分级分析：

## 背景信息
需求描述: "{requirement_text}"
需求维度: {dimension}
缺失方面: {aspect}

## 分级任务
请从以下维度评估这个缺失方面：

1. 优先级评估 (关键/重要/一般/可选):
   - 关键: 不澄清就无法继续开发
   - 重要: 影响核心功能，强烈建议澄清
   - 一般: 影响用户体验，建议澄清
   - 可选: 优化项，可以暂缓

2. 影响范围 (核心业务/用户体验/系统质量/维护性):
   - 核心业务: 直接影响主要业务流程
   - 用户体验: 影响用户使用感受
   - 系统质量: 影响性能、安全、可靠性
   - 维护性: 影响后期维护和扩展

3. 风险级别 (高风险/中风险/低风险):
   - 高风险: 可能导致项目失败或重大返工
   - 中风险: 可能需要局部调整
   - 低风险: 影响有限

4. 业务影响度 (0-1的数值):
   评估对整体业务目标实现的影响程度

5. 澄清难度 (简单/中等/复杂):
   评估澄清这个方面需要的工作量

## 输出格式
请返回JSON格式：
{{
    "priority": "关键/重要/一般/可选",
    "impact_scope": "核心业务/用户体验/系统质量/维护性",
    "risk_level": "高风险/中风险/低风险",
    "business_impact": 0.85,
    "clarification_effort": "简单/中等/复杂",
    "suggested_questions": [
        "具体的澄清问题1",
        "具体的澄清问题2"
    ],
    "rationale": "分级理由的详细说明"
}}"""

        try:
            from app.llm import LLM
            from app.schema import Message

            llm = LLM()
            messages = [Message.user_message(prompt)]

            response = await llm.ask(
                messages=messages,
                temperature=0.2,  # 保持一致性
                stream=False,
            )

            # 解析LLM响应
            analysis_result = self._parse_json_response(response)

            # 映射到枚举类型
            priority_map = {
                "关键": MissingAspectPriority.CRITICAL,
                "重要": MissingAspectPriority.HIGH,
                "一般": MissingAspectPriority.MEDIUM,
                "可选": MissingAspectPriority.LOW,
            }

            impact_map = {
                "核心业务": ImpactScope.CORE_BUSINESS,
                "用户体验": ImpactScope.USER_EXPERIENCE,
                "系统质量": ImpactScope.SYSTEM_QUALITY,
                "维护性": ImpactScope.MAINTENANCE,
            }

            risk_map = {
                "高风险": RiskLevel.HIGH_RISK,
                "中风险": RiskLevel.MEDIUM_RISK,
                "低风险": RiskLevel.LOW_RISK,
            }

            return MissingAspectClassification(
                aspect=aspect,
                priority=priority_map.get(
                    analysis_result.get("priority", "一般"),
                    MissingAspectPriority.MEDIUM,
                ),
                impact_scope=impact_map.get(
                    analysis_result.get("impact_scope", "用户体验"),
                    ImpactScope.USER_EXPERIENCE,
                ),
                risk_level=risk_map.get(
                    analysis_result.get("risk_level", "中风险"), RiskLevel.MEDIUM_RISK
                ),
                business_impact=float(analysis_result.get("business_impact", 0.5)),
                clarification_effort=analysis_result.get(
                    "clarification_effort", "中等"
                ),
                suggested_questions=analysis_result.get("suggested_questions", []),
                rationale=analysis_result.get("rationale", "默认分级"),
            )

        except Exception as e:
            logger.error(f"缺失方面分级分析失败: {e}")
            # 返回默认分级
            return MissingAspectClassification(
                aspect=aspect,
                priority=MissingAspectPriority.MEDIUM,
                impact_scope=ImpactScope.USER_EXPERIENCE,
                risk_level=RiskLevel.MEDIUM_RISK,
                business_impact=0.5,
                clarification_effort="中等",
                suggested_questions=[f"请详细说明{aspect}的具体要求"],
                rationale="分析异常，使用默认分级",
            )

    def _get_priority_weight(self, priority: MissingAspectPriority) -> int:
        """获取优先级权重"""
        weights = {
            MissingAspectPriority.CRITICAL: 4,
            MissingAspectPriority.HIGH: 3,
            MissingAspectPriority.MEDIUM: 2,
            MissingAspectPriority.LOW: 1,
        }
        return weights.get(priority, 2)

    def _get_risk_weight(self, risk: RiskLevel) -> int:
        """获取风险权重"""
        weights = {
            RiskLevel.HIGH_RISK: 3,
            RiskLevel.MEDIUM_RISK: 2,
            RiskLevel.LOW_RISK: 1,
        }
        return weights.get(risk, 2)

    async def assess_design_readiness(
        self, requirement_text: str, quality_analysis: Dict
    ) -> Dict:
        """
        评估需求的设计就绪度
        基于"能否支撑后续设计和开发"的标准
        """
        logger.info("🎯 评估需求设计就绪度...")

        # 评估各个可设计性维度
        readiness_prompt = f"""作为软件架构师，请评估以下需求是否足以支撑后续的系统设计和开发：

需求文本："{requirement_text}"

请从以下5个维度评估（0-1分）：

1. **架构设计可行性** (0-1)：
   - 能否基于此需求设计系统架构？
   - 非功能需求是否明确？
   - 技术选型是否有指导意义？
   评分标准：
   - 0.8-1.0: 可以直接进行架构设计
   - 0.6-0.8: 基本可行，需要少量补充
   - 0.4-0.6: 需要大量补充才能设计
   - 0.0-0.4: 无法进行架构设计

2. **实现指导清晰性** (0-1)：
   - 开发人员能否基于此需求编码？
   - 功能边界是否清晰？
   - 业务规则是否完整？
   评分标准：
   - 0.8-1.0: 可以直接指导开发
   - 0.6-0.8: 基本清晰，需要少量澄清
   - 0.4-0.6: 需要大量澄清
   - 0.0-0.4: 无法指导开发

3. **测试完整性** (0-1)：
   - 能否基于此需求制定测试用例？
   - 验收条件是否可量化？
   - 异常场景是否考虑？
   评分标准：
   - 0.8-1.0: 可以制定完整测试用例
   - 0.6-0.8: 可以制定基本测试用例
   - 0.4-0.6: 测试用例不完整
   - 0.0-0.4: 无法制定测试用例

4. **项目可控性** (0-1)：
   - 工作量是否可估算？
   - 风险是否可识别？
   - 里程碑是否可制定？
   评分标准：
   - 0.8-1.0: 项目完全可控
   - 0.6-0.8: 基本可控
   - 0.4-0.6: 部分可控
   - 0.0-0.4: 项目不可控

5. **风险识别度** (0-1)：
   - 技术风险是否可识别？
   - 业务风险是否清楚？
   - 依赖关系是否明确？

返回JSON格式：
{{
    "architecture_feasibility": 0.7,
    "implementation_clarity": 0.6,
    "testing_completeness": 0.5,
    "project_controllability": 0.4,
    "risk_identification": 0.6,
    "overall_readiness": 0.58,
    "readiness_level": "不足",
    "blocking_issues": ["缺少非功能需求", "业务规则不明确"],
    "next_actions": ["澄清性能要求", "明确业务流程"]
}}"""

        try:
            response = await self.llm.ask(
                messages=[{"role": "user", "content": readiness_prompt}],
                temperature=0.1,
                stream=False,
            )

            result = self._parse_json_response(response)

            # 计算综合设计就绪度
            design_config = self.config["design_readiness"]
            overall_readiness = (
                result.get("architecture_feasibility", 0)
                * design_config["architecture_feasibility"]
                + result.get("implementation_clarity", 0)
                * design_config["implementation_clarity"]
                + result.get("testing_completeness", 0)
                * design_config["testing_completeness"]
                + result.get("project_controllability", 0)
                * design_config["project_controllability"]
                + result.get("risk_identification", 0)
                * design_config["risk_identification"]
            )

            # 确定就绪级别
            if overall_readiness >= 0.90:
                readiness_level = "优秀"
            elif overall_readiness >= 0.80:
                readiness_level = "良好"
            elif overall_readiness >= 0.70:
                readiness_level = "基本达标"
            elif overall_readiness >= 0.60:
                readiness_level = "需要改进"
            else:
                readiness_level = "严重不足"

            result["overall_readiness"] = overall_readiness
            result["readiness_level"] = readiness_level

            logger.info(
                f"🎯 设计就绪度评估: {overall_readiness:.2f} ({readiness_level})"
            )

            return result

        except Exception as e:
            logger.error(f"设计就绪度评估失败: {e}")
            return {
                "architecture_feasibility": 0.3,
                "implementation_clarity": 0.3,
                "testing_completeness": 0.3,
                "project_controllability": 0.3,
                "risk_identification": 0.3,
                "overall_readiness": 0.3,
                "readiness_level": "评估失败",
                "blocking_issues": ["评估系统异常"],
                "next_actions": ["重新评估"],
            }

    async def analyze_knowledge_and_code_conflicts(
        self, requirement_text: str, quality_analysis: Dict
    ) -> Dict:
        """
        分析需求与知识库、代码库的冲突
        实现智能化的冲突检测和差异处理
        """
        logger.info("🔍 开始知识库和代码库冲突分析...")

        try:
            # 1. 知识库冲突分析
            knowledge_conflicts = await self._analyze_knowledge_conflicts(
                requirement_text
            )

            # 2. 代码库冲突分析
            codebase_conflicts = await self._analyze_codebase_conflicts(
                requirement_text
            )

            # 3. 综合冲突评估
            conflict_summary = self._synthesize_conflict_analysis(
                knowledge_conflicts, codebase_conflicts, requirement_text
            )

            logger.info(
                f"🔍 冲突分析完成，发现 {len(conflict_summary.get('critical_conflicts', []))} 个严重冲突"
            )

            return conflict_summary

        except Exception as e:
            logger.error(f"冲突分析失败: {e}")
            return {
                "knowledge_conflicts": [],
                "codebase_conflicts": [],
                "critical_conflicts": [],
                "manageable_differences": [],
                "conflict_resolution_suggestions": [],
                "overall_conflict_level": "unknown",
            }

    async def _analyze_knowledge_conflicts(self, requirement_text: str) -> Dict:
        """分析与知识库的冲突"""

        # 调用知识库服务搜索相关知识
        try:
            from app.modules.knowledge_base.service import KnowledgeService
            from app.modules.knowledge_base.types import KnowledgeQuery, KnowledgeType

            knowledge_service = KnowledgeService()

            # 搜索相关知识（使用正确的API）
            knowledge_query = KnowledgeQuery(
                query_text=requirement_text,
                knowledge_types=[
                    KnowledgeType.REQUIREMENTS_TEMPLATES,
                    KnowledgeType.BEST_PRACTICES,
                ],
                min_confidence=0.5,
                limit=10,
            )
            search_results = knowledge_service.search_knowledge(knowledge_query)

            # 构建知识库分析提示
            relevant_knowledge = ""
            if (
                search_results
                and hasattr(search_results, "results")
                and search_results.results
            ):
                relevant_knowledge = "\n".join(
                    [
                        f"- {result.entry.title}: {result.entry.summary}"
                        for result in search_results.results[:5]
                    ]
                )
            else:
                relevant_knowledge = "未找到相关知识库内容"

        except Exception as e:
            logger.warning(f"知识库查询失败: {e}")
            relevant_knowledge = "知识库查询异常"

        knowledge_prompt = f"""作为知识管理专家，请分析用户需求与已有知识库的冲突情况：

用户需求："{requirement_text}"

相关知识库内容：
{relevant_knowledge}

请分析以下类型的冲突：

1. **硬冲突**（不可接受的冲突）：
   - 违反既定标准或规范
   - 与核心架构原则冲突
   - 与安全要求相冲突

2. **软冲突**（可协商的差异）：
   - 与现有最佳实践不同
   - 需要新的技术方案
   - 超出现有经验范围

3. **创新需求**（合理的新需求）：
   - 业务发展的新要求
   - 技术演进的新机会
   - 用户体验的新期望

返回JSON格式：
{{
    "hard_conflicts": [
        {{
            "conflict_type": "安全冲突",
            "description": "需求要求明文存储密码，违反安全规范",
            "severity": "critical",
            "knowledge_source": "安全最佳实践",
            "resolution_required": true
        }}
    ],
    "soft_conflicts": [
        {{
            "conflict_type": "技术选型差异",
            "description": "需求建议使用新技术栈，与现有技术不同",
            "severity": "medium",
            "knowledge_source": "技术标准",
            "negotiable": true
        }}
    ],
    "innovation_opportunities": [
        {{
            "opportunity_type": "业务创新",
            "description": "AI辅助功能是新的业务机会",
            "potential_value": "high",
            "knowledge_gap": "需要补充AI相关知识"
        }}
    ],
    "knowledge_coverage": 0.75,
    "recommendation": "重点关注安全冲突，其他差异可通过协商解决"
}}"""

        try:
            response = await self.llm.ask(
                messages=[{"role": "user", "content": knowledge_prompt}],
                temperature=0.1,
                stream=False,
            )

            return self._parse_json_response(response)

        except Exception as e:
            logger.error(f"知识库冲突分析失败: {e}")
            return {
                "hard_conflicts": [],
                "soft_conflicts": [],
                "innovation_opportunities": [],
                "knowledge_coverage": 0.0,
                "recommendation": "知识库分析异常",
            }

    async def _analyze_codebase_conflicts(self, requirement_text: str) -> Dict:
        """分析与代码库的冲突"""

        # 调用代码分析器
        try:
            from app.assistants.requirements.code_analyzer import CodeAnalyzer

            code_analyzer = CodeAnalyzer()

            # 分析代码库（使用相对路径，避免系统文件）
            import os

            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            code_analyzer = CodeAnalyzer(project_root=current_dir)
            analysis_result = code_analyzer.analyze_codebase(["app/"])

            # 提取关键信息
            project_overview = analysis_result.get("project_overview", {})
            codebase_summary = f"""
代码库规模: {project_overview.get('total_files', 0)} 个文件
主要语言: {', '.join(project_overview.get('languages', {}).keys())}
识别组件: {len(analysis_result.get('components', []))} 个
设计模式: {', '.join([p.get('name', '') for p in analysis_result.get('patterns', [])][:3])}
"""

        except Exception as e:
            logger.warning(f"代码库分析失败: {e}")
            codebase_summary = "代码库分析异常"

        codebase_prompt = f"""作为代码架构专家，请分析用户需求与现有代码库的冲突情况：

用户需求："{requirement_text}"

代码库分析：
{codebase_summary}

请分析以下冲突类型：

1. **架构冲突**（需要重大重构）：
   - 违反现有架构原则
   - 需要破坏性变更
   - 与核心设计模式冲突

2. **技术债务**（需要代码改进）：
   - 现有代码质量限制
   - 需要重构优化
   - 技术栈不兼容

3. **扩展机会**（可扩展实现）：
   - 基于现有架构扩展
   - 复用现有组件
   - 渐进式实现

返回JSON格式：
{{
    "architecture_conflicts": [
        {{
            "conflict_type": "模块架构冲突",
            "description": "需求要求的功能与现有模块设计冲突",
            "affected_modules": ["模块1", "模块2"],
            "refactoring_required": "major",
            "estimated_effort": "2-3个月"
        }}
    ],
    "technical_debt": [
        {{
            "debt_type": "代码质量问题",
            "description": "现有代码缺少测试覆盖",
            "impact_on_requirement": "增加开发风险",
            "improvement_needed": "添加单元测试"
        }}
    ],
    "extension_opportunities": [
        {{
            "opportunity_type": "组件复用",
            "description": "可以复用现有用户管理组件",
            "reusable_components": ["UserManager", "AuthService"],
            "implementation_approach": "扩展现有接口"
        }}
    ],
    "overall_compatibility": 0.70,
    "implementation_feasibility": "medium"
}}"""

        try:
            response = await self.llm.ask(
                messages=[{"role": "user", "content": codebase_prompt}],
                temperature=0.1,
                stream=False,
            )

            return self._parse_json_response(response)

        except Exception as e:
            logger.error(f"代码库冲突分析失败: {e}")
            return {
                "architecture_conflicts": [],
                "technical_debt": [],
                "extension_opportunities": [],
                "overall_compatibility": 0.0,
                "implementation_feasibility": "unknown",
            }

    def _synthesize_conflict_analysis(
        self, knowledge_conflicts: Dict, codebase_conflicts: Dict, requirement_text: str
    ) -> Dict:
        """综合冲突分析，生成处理建议"""

        # 提取关键冲突
        critical_conflicts = []
        manageable_differences = []

        # 处理知识库冲突
        for conflict in knowledge_conflicts.get("hard_conflicts", []):
            critical_conflicts.append(
                {
                    "type": "knowledge",
                    "category": conflict.get("conflict_type", ""),
                    "description": conflict.get("description", ""),
                    "severity": conflict.get("severity", "medium"),
                    "source": "knowledge_base",
                }
            )

        for conflict in knowledge_conflicts.get("soft_conflicts", []):
            manageable_differences.append(
                {
                    "type": "knowledge",
                    "category": conflict.get("conflict_type", ""),
                    "description": conflict.get("description", ""),
                    "negotiable": conflict.get("negotiable", True),
                    "source": "knowledge_base",
                }
            )

        # 处理代码库冲突
        for conflict in codebase_conflicts.get("architecture_conflicts", []):
            if conflict.get("refactoring_required") == "major":
                critical_conflicts.append(
                    {
                        "type": "codebase",
                        "category": "architecture",
                        "description": conflict.get("description", ""),
                        "severity": "critical",
                        "source": "codebase",
                    }
                )
            else:
                manageable_differences.append(
                    {
                        "type": "codebase",
                        "category": "architecture",
                        "description": conflict.get("description", ""),
                        "refactoring_effort": conflict.get(
                            "estimated_effort", "unknown"
                        ),
                        "source": "codebase",
                    }
                )

        # 生成解决建议
        resolution_suggestions = self._generate_conflict_resolution_suggestions(
            critical_conflicts, manageable_differences
        )

        # 确定整体冲突级别
        if len(critical_conflicts) > 0:
            overall_level = "critical"
        elif len(manageable_differences) > 3:
            overall_level = "medium"
        else:
            overall_level = "low"

        return {
            "knowledge_conflicts": knowledge_conflicts,
            "codebase_conflicts": codebase_conflicts,
            "critical_conflicts": critical_conflicts,
            "manageable_differences": manageable_differences,
            "conflict_resolution_suggestions": resolution_suggestions,
            "overall_conflict_level": overall_level,
            "total_conflicts": len(critical_conflicts) + len(manageable_differences),
            "requires_stakeholder_decision": len(critical_conflicts) > 0,
        }

    def _generate_conflict_resolution_suggestions(
        self, critical_conflicts: List, manageable_differences: List
    ) -> List[str]:
        """生成冲突解决建议"""
        suggestions = []

        if critical_conflicts:
            suggestions.append("🚨 发现严重冲突，需要利益相关者决策")
            suggestions.append("📋 建议召开技术评审会议讨论解决方案")

        if any(c.get("type") == "knowledge" for c in critical_conflicts):
            suggestions.append("📚 需要更新知识库或调整需求以符合最佳实践")

        if any(c.get("type") == "codebase" for c in critical_conflicts):
            suggestions.append("🔧 需要架构重构或寻找替代技术方案")

        if manageable_differences:
            suggestions.append("🤝 可通过技术协商解决部分差异")
            suggestions.append("📈 建议采用渐进式实现策略")

        if not critical_conflicts and len(manageable_differences) <= 2:
            suggestions.append("✅ 冲突可控，可以正常推进需求实现")

        return suggestions
