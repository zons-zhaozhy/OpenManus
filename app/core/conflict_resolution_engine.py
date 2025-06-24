"""
智能冲突解决引擎 - OpenManus需求分析系统

实现科学的冲突检测和差异处理机制：
1. 智能区分"冲突"和"合理差异"
2. 提供渐进式冲突解决策略
3. 支持利益相关者决策支持
4. 基于知识库和代码库的智能建议
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.config_manager import ConfigManager
from app.llm import LLM
from app.logger import logger


class ConflictType(Enum):
    """冲突类型"""

    KNOWLEDGE_CONFLICT = "knowledge_conflict"  # 知识库冲突
    CODEBASE_CONFLICT = "codebase_conflict"  # 代码库冲突
    ARCHITECTURE_CONFLICT = "architecture_conflict"  # 架构冲突
    SECURITY_CONFLICT = "security_conflict"  # 安全冲突
    BUSINESS_CONFLICT = "business_conflict"  # 业务冲突


class ConflictSeverity(Enum):
    """冲突严重级别"""

    CRITICAL = "critical"  # 严重冲突，必须解决
    HIGH = "high"  # 高级冲突，强烈建议解决
    MEDIUM = "medium"  # 中等冲突，建议协商
    LOW = "low"  # 轻微冲突，可接受


class DifferenceNature(Enum):
    """差异性质"""

    INCOMPATIBLE_CONFLICT = "incompatible"  # 不兼容冲突（硬冲突）
    NEGOTIABLE_DIFFERENCE = "negotiable"  # 可协商差异（软冲突）
    INNOVATION_OPPORTUNITY = "innovation"  # 创新机会（合理差异）
    TEMPORARY_DEVIATION = "temporary"  # 临时偏差（可接受）


@dataclass
class ConflictItem:
    """冲突项"""

    id: str
    type: ConflictType
    severity: ConflictSeverity
    nature: DifferenceNature
    description: str
    affected_areas: List[str]
    source_knowledge: str
    requirement_aspect: str
    business_impact: float  # 0-1
    technical_impact: float  # 0-1
    risk_level: float  # 0-1


@dataclass
class ResolutionStrategy:
    """解决策略"""

    strategy_id: str
    conflict_id: str
    approach: str  # "requirement_adjustment", "knowledge_update", "architecture_refactor", "stakeholder_decision"
    description: str
    pros: List[str]
    cons: List[str]
    effort_estimate: str  # "low", "medium", "high"
    timeline_estimate: str
    success_probability: float  # 0-1
    recommended: bool


@dataclass
class ConflictResolutionPlan:
    """冲突解决方案"""

    plan_id: str
    conflicts: List[ConflictItem]
    strategies: List[ResolutionStrategy]
    recommended_sequence: List[str]  # 推荐执行顺序
    stakeholder_decisions_required: List[str]
    overall_resolution_score: float
    implementation_roadmap: Dict[str, Any]


class ConflictResolutionEngine:
    """智能冲突解决引擎"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = {}
        self.llm = LLM()

        # 冲突处理配置
        self.conflict_config = self.config.get(
            "conflict_resolution",
            {
                "severity_weights": {
                    "critical": 1.0,
                    "high": 0.8,
                    "medium": 0.6,
                    "low": 0.3,
                },
                "nature_weights": {
                    "incompatible": 1.0,
                    "negotiable": 0.7,
                    "innovation": 0.4,
                    "temporary": 0.2,
                },
                "auto_resolution_threshold": 0.3,  # 低于此阈值可自动处理
                "stakeholder_decision_threshold": 0.8,  # 高于此阈值需要利益相关者决策
            },
        )

    async def analyze_conflicts_comprehensive(
        self, requirement_text: str, knowledge_conflicts: Dict, codebase_conflicts: Dict
    ) -> ConflictResolutionPlan:
        """
        综合冲突分析和解决方案制定
        """
        logger.info("🔍 开始综合冲突分析...")

        # 1. 提取和分类冲突
        conflicts = await self._extract_and_classify_conflicts(
            requirement_text, knowledge_conflicts, codebase_conflicts
        )

        # 2. 为每个冲突生成解决策略
        all_strategies = []
        for conflict in conflicts:
            strategies = await self._generate_resolution_strategies(
                conflict, requirement_text
            )
            all_strategies.extend(strategies)

        # 3. 制定整体解决方案
        resolution_plan = await self._create_resolution_plan(conflicts, all_strategies)

        logger.info(
            f"🔍 冲突分析完成，识别 {len(conflicts)} 个冲突，生成 {len(all_strategies)} 个策略"
        )

        return resolution_plan

    async def _extract_and_classify_conflicts(
        self, requirement_text: str, knowledge_conflicts: Dict, codebase_conflicts: Dict
    ) -> List[ConflictItem]:
        """提取和分类所有冲突"""
        conflicts = []

        # 处理知识库冲突
        for hard_conflict in knowledge_conflicts.get("hard_conflicts", []):
            conflict = ConflictItem(
                id=f"kb_hard_{len(conflicts)}",
                type=ConflictType.KNOWLEDGE_CONFLICT,
                severity=ConflictSeverity.CRITICAL,
                nature=DifferenceNature.INCOMPATIBLE_CONFLICT,
                description=hard_conflict.get("description", ""),
                affected_areas=[hard_conflict.get("conflict_type", "")],
                source_knowledge=hard_conflict.get("knowledge_source", ""),
                requirement_aspect=requirement_text[:100],
                business_impact=0.8,
                technical_impact=0.7,
                risk_level=0.9,
            )
            conflicts.append(conflict)

        for soft_conflict in knowledge_conflicts.get("soft_conflicts", []):
            conflict = ConflictItem(
                id=f"kb_soft_{len(conflicts)}",
                type=ConflictType.KNOWLEDGE_CONFLICT,
                severity=ConflictSeverity.MEDIUM,
                nature=DifferenceNature.NEGOTIABLE_DIFFERENCE,
                description=soft_conflict.get("description", ""),
                affected_areas=[soft_conflict.get("conflict_type", "")],
                source_knowledge=soft_conflict.get("knowledge_source", ""),
                requirement_aspect=requirement_text[:100],
                business_impact=0.5,
                technical_impact=0.6,
                risk_level=0.4,
            )
            conflicts.append(conflict)

        # 处理代码库冲突
        for arch_conflict in codebase_conflicts.get("architecture_conflicts", []):
            severity = (
                ConflictSeverity.CRITICAL
                if arch_conflict.get("refactoring_required") == "major"
                else ConflictSeverity.HIGH
            )
            nature = (
                DifferenceNature.INCOMPATIBLE_CONFLICT
                if severity == ConflictSeverity.CRITICAL
                else DifferenceNature.NEGOTIABLE_DIFFERENCE
            )

            conflict = ConflictItem(
                id=f"cb_arch_{len(conflicts)}",
                type=ConflictType.ARCHITECTURE_CONFLICT,
                severity=severity,
                nature=nature,
                description=arch_conflict.get("description", ""),
                affected_areas=arch_conflict.get("affected_modules", []),
                source_knowledge="代码库架构",
                requirement_aspect=requirement_text[:100],
                business_impact=0.7,
                technical_impact=0.9,
                risk_level=0.8 if severity == ConflictSeverity.CRITICAL else 0.5,
            )
            conflicts.append(conflict)

        return conflicts

    async def _generate_resolution_strategies(
        self, conflict: ConflictItem, requirement_text: str
    ) -> List[ResolutionStrategy]:
        """为单个冲突生成解决策略"""

        prompt = f"""作为冲突解决专家，请为以下冲突制定多种解决策略：

## 冲突信息
类型: {conflict.type.value}
严重程度: {conflict.severity.value}
性质: {conflict.nature.value}
描述: {conflict.description}
影响范围: {', '.join(conflict.affected_areas)}
来源: {conflict.source_knowledge}

## 需求上下文
需求: {requirement_text}

## 策略要求
请提供3-4种不同的解决策略，包括：
1. 需求调整策略
2. 知识库/代码库更新策略
3. 架构重构策略（如适用）
4. 利益相关者决策策略

每种策略需要评估：
- 优缺点分析
- 实施难度
- 时间估算
- 成功概率
- 是否推荐

返回JSON格式：
{{
    "strategies": [
        {{
            "approach": "requirement_adjustment",
            "description": "调整需求以符合现有标准",
            "pros": ["优点1", "优点2"],
            "cons": ["缺点1", "缺点2"],
            "effort_estimate": "low/medium/high",
            "timeline_estimate": "1-2周",
            "success_probability": 0.85,
            "recommended": true
        }}
    ]
}}"""

        try:
            response = await self.llm.ask(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                stream=False,
            )

            import json

            result = json.loads(response)

            strategies = []
            for i, strategy_data in enumerate(result.get("strategies", [])):
                strategy = ResolutionStrategy(
                    strategy_id=f"{conflict.id}_strategy_{i}",
                    conflict_id=conflict.id,
                    approach=strategy_data.get("approach", "unknown"),
                    description=strategy_data.get("description", ""),
                    pros=strategy_data.get("pros", []),
                    cons=strategy_data.get("cons", []),
                    effort_estimate=strategy_data.get("effort_estimate", "medium"),
                    timeline_estimate=strategy_data.get("timeline_estimate", "未估算"),
                    success_probability=strategy_data.get("success_probability", 0.5),
                    recommended=strategy_data.get("recommended", False),
                )
                strategies.append(strategy)

            return strategies

        except Exception as e:
            logger.error(f"生成解决策略失败: {e}")
            # 返回默认策略
            return [
                ResolutionStrategy(
                    strategy_id=f"{conflict.id}_default",
                    conflict_id=conflict.id,
                    approach="stakeholder_decision",
                    description="需要利益相关者决策",
                    pros=["确保决策正确性"],
                    cons=["耗时较长"],
                    effort_estimate="high",
                    timeline_estimate="1-2周",
                    success_probability=0.7,
                    recommended=True,
                )
            ]

    async def _create_resolution_plan(
        self, conflicts: List[ConflictItem], strategies: List[ResolutionStrategy]
    ) -> ConflictResolutionPlan:
        """制定整体解决方案"""

        # 计算整体解决评分
        total_conflicts = len(conflicts)
        resolvable_conflicts = len(
            [c for c in conflicts if c.severity != ConflictSeverity.CRITICAL]
        )
        overall_score = (
            resolvable_conflicts / total_conflicts if total_conflicts > 0 else 1.0
        )

        # 确定需要利益相关者决策的事项
        stakeholder_decisions = []
        for conflict in conflicts:
            if conflict.severity == ConflictSeverity.CRITICAL:
                stakeholder_decisions.append(
                    f"解决{conflict.type.value}: {conflict.description[:50]}"
                )

        # 推荐执行顺序
        strategy_by_priority = sorted(
            strategies,
            key=lambda s: (
                s.success_probability * (1 if s.recommended else 0.5),
                -self._get_effort_weight(s.effort_estimate),
            ),
            reverse=True,
        )

        recommended_sequence = [s.strategy_id for s in strategy_by_priority[:5]]

        # 实施路线图
        implementation_roadmap = {
            "immediate_actions": [
                s.description
                for s in strategy_by_priority[:2]
                if s.effort_estimate == "low"
            ],
            "short_term": [
                s.description
                for s in strategy_by_priority
                if s.effort_estimate == "medium"
            ],
            "long_term": [
                s.description
                for s in strategy_by_priority
                if s.effort_estimate == "high"
            ],
            "stakeholder_decisions": stakeholder_decisions,
        }

        return ConflictResolutionPlan(
            plan_id=f"resolution_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            conflicts=conflicts,
            strategies=strategies,
            recommended_sequence=recommended_sequence,
            stakeholder_decisions_required=stakeholder_decisions,
            overall_resolution_score=overall_score,
            implementation_roadmap=implementation_roadmap,
        )

    def _get_effort_weight(self, effort: str) -> float:
        """获取工作量权重"""
        weights = {"low": 1.0, "medium": 2.0, "high": 3.0}
        return weights.get(effort, 2.0)

    def classify_difference_nature(
        self, conflict_description: str, requirement_context: str
    ) -> DifferenceNature:
        """
        智能区分冲突性质：硬冲突 vs 软差异 vs 创新机会
        """
        # 安全相关 - 通常是硬冲突
        if any(
            keyword in conflict_description.lower()
            for keyword in ["安全", "密码", "加密", "权限", "认证", "漏洞"]
        ):
            return DifferenceNature.INCOMPATIBLE_CONFLICT

        # 架构原则相关 - 通常是硬冲突
        if any(
            keyword in conflict_description.lower()
            for keyword in ["架构", "模式", "设计原则", "核心逻辑"]
        ):
            return DifferenceNature.INCOMPATIBLE_CONFLICT

        # 技术选型差异 - 通常是可协商的
        if any(
            keyword in conflict_description.lower()
            for keyword in ["技术栈", "框架", "工具", "版本"]
        ):
            return DifferenceNature.NEGOTIABLE_DIFFERENCE

        # 业务创新 - 通常是机会
        if any(
            keyword in conflict_description.lower()
            for keyword in ["AI", "智能", "创新", "新功能", "增强"]
        ):
            return DifferenceNature.INNOVATION_OPPORTUNITY

        # 默认为可协商差异
        return DifferenceNature.NEGOTIABLE_DIFFERENCE

    def generate_stakeholder_decision_matrix(
        self, conflicts: List[ConflictItem]
    ) -> Dict[str, Any]:
        """
        生成利益相关者决策矩阵
        """
        critical_conflicts = [
            c for c in conflicts if c.severity == ConflictSeverity.CRITICAL
        ]

        decision_matrix = {
            "total_conflicts": len(conflicts),
            "critical_conflicts": len(critical_conflicts),
            "business_impact_score": (
                sum(c.business_impact for c in conflicts) / len(conflicts)
                if conflicts
                else 0
            ),
            "technical_impact_score": (
                sum(c.technical_impact for c in conflicts) / len(conflicts)
                if conflicts
                else 0
            ),
            "risk_score": (
                sum(c.risk_level for c in conflicts) / len(conflicts)
                if conflicts
                else 0
            ),
            "decision_urgency": "high" if len(critical_conflicts) > 0 else "medium",
            "recommended_approach": (
                "stakeholder_meeting"
                if len(critical_conflicts) > 2
                else "technical_review"
            ),
            "key_decision_points": [
                f"{c.type.value}: {c.description}" for c in critical_conflicts
            ],
        }

        return decision_matrix
