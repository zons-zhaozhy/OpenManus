"""
需求质量评估器
负责评估需求在各个维度的质量，支持质量驱动的澄清策略
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

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


class QualityAssessor:
    """需求质量评估器"""

    def __init__(self):
        self.llm = LLM()
        self.config = REQUIREMENT_QUALITY_CONFIG

        # 质量阈值
        self.quality_threshold = self.config["quality_thresholds"]["overall_threshold"]
        self.dimension_threshold = self.config["quality_thresholds"][
            "dimension_threshold"
        ]
        self.excellent_threshold = self.config["quality_thresholds"][
            "excellent_threshold"
        ]

        # 维度权重
        self.dimension_weights = self.config["dimension_weights"]

        # 评分严格度配置
        self.scoring_config = self.config["scoring_strictness"]

    async def analyze_requirement_quality(
        self, requirement_text: str, clarification_history: List[Dict] = None
    ) -> Dict[RequirementDimension, DimensionQuality]:
        """
        分析需求质量 - 多维度并行评估
        """
        logger.info("🎯 开始多维度需求质量分析...")

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
   - 0.7-1.0: 具体详细，可执行
   - 0.5-0.7: 有一定细节
   - 0.3-0.5: 较为抽象，需要具体化
   - 0.0-0.3: 过于笼统

4. 可行性（0-1）：
   - 0.7-1.0: 技术可行，资源合理
   - 0.5-0.7: 基本可行，有挑战
   - 0.3-0.5: 可行性存疑
   - 0.0-0.3: 不可行或风险极高

请返回JSON格式：
{{
    "completeness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "specificity": 0.0-1.0,
    "feasibility": 0.0-1.0,
    "missing_aspects": ["缺失方面1", "缺失方面2"],
    "improvement_suggestions": ["改进建议1", "改进建议2"]
}}
"""

        try:
            response = await self.llm.achat(prompt)
            analysis = self._parse_json_response(response)

            # 计算综合评分
            overall_score = (
                analysis["completeness"] * 0.3
                + analysis["clarity"] * 0.25
                + analysis["specificity"] * 0.25
                + analysis["feasibility"] * 0.2
            )

            return DimensionQuality(
                dimension=dimension,
                completeness=analysis["completeness"],
                clarity=analysis["clarity"],
                specificity=analysis["specificity"],
                feasibility=analysis["feasibility"],
                overall_score=overall_score,
                missing_aspects=analysis.get("missing_aspects", []),
                improvement_suggestions=analysis.get("improvement_suggestions", []),
            )

        except Exception as e:
            logger.error(f"维度 {dimension.value} 质量分析失败: {e}")
            # 返回默认的低质量评估
            return DimensionQuality(
                dimension=dimension,
                completeness=0.3,
                clarity=0.3,
                specificity=0.3,
                feasibility=0.5,
                overall_score=0.3,
                missing_aspects=[f"{dimension.value}信息不足"],
                improvement_suggestions=[f"请补充{dimension.value}相关信息"],
            )

    def _calculate_overall_quality(
        self, quality_assessment: Dict[RequirementDimension, DimensionQuality]
    ) -> float:
        """
        计算需求整体质量分数
        """
        if not quality_assessment:
            return 0.0

        # 加权计算整体质量
        total_weighted_score = 0.0
        total_weight = 0.0

        for dimension, quality in quality_assessment.items():
            weight = self.dimension_weights.get(dimension.value, 1.0)
            total_weighted_score += quality.overall_score * weight
            total_weight += weight

        # 避免除零错误
        if total_weight == 0:
            return 0.0

        overall_score = total_weighted_score / total_weight

        logger.info(f"质量评估详情:")
        for dimension, quality in quality_assessment.items():
            logger.info(f"  {dimension.value}: {quality.overall_score:.2f}")

        return overall_score

    def _parse_json_response(self, response: str) -> Dict:
        """解析LLM的JSON响应"""
        try:
            import json

            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # 尝试提取JSON部分
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
                else:
                    logger.warning(f"无法提取JSON: {response}")
                    return self._get_default_response()
            except Exception as e:
                logger.error(f"JSON解析失败: {e}")
                return self._get_default_response()
        except Exception as e:
            logger.error(f"解析响应失败: {e}")
            return self._get_default_response()

    def _get_default_response(self) -> Dict:
        """返回默认响应"""
        return {
            "completeness": 0.5,
            "clarity": 0.5,
            "specificity": 0.5,
            "feasibility": 0.7,
            "missing_aspects": ["需要更多信息"],
            "improvement_suggestions": ["请提供更详细的描述"],
        }

    def should_continue_clarification(
        self,
        quality_assessment: Dict[RequirementDimension, DimensionQuality],
        current_round: int,
    ) -> tuple[bool, str]:
        """
        判断是否需要继续澄清

        Returns:
            (should_continue: bool, reason: str)
        """
        overall_quality = self._calculate_overall_quality(quality_assessment)

        # 获取配置参数
        max_rounds = self.config["clarification_rounds"]["max_rounds"]
        min_rounds = self.config["clarification_rounds"]["min_rounds"]
        early_stop_threshold = self.config["clarification_rounds"][
            "early_stop_threshold"
        ]

        # 轮次限制检查
        if current_round >= max_rounds:
            return False, f"已达到最大澄清轮次 ({max_rounds})"

        # 质量满足检查
        if overall_quality >= early_stop_threshold and current_round >= min_rounds:
            return (
                False,
                f"质量已达标 ({overall_quality:.2f} >= {early_stop_threshold})",
            )

        # 检查是否有关键维度质量过低
        critical_issues = []
        for dimension, quality in quality_assessment.items():
            if quality.overall_score < self.dimension_threshold:
                critical_issues.append(
                    f"{dimension.value}({quality.overall_score:.2f})"
                )

        if critical_issues:
            return True, f"关键维度质量不足: {', '.join(critical_issues)}"

        if overall_quality < self.quality_threshold:
            return (
                True,
                f"整体质量不足 ({overall_quality:.2f} < {self.quality_threshold})",
            )

        return False, f"质量基本满足要求 ({overall_quality:.2f})"
