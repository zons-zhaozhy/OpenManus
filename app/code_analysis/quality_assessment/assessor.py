"""
代码质量评估器
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.logger import logger

from ..models.base import CodeComponent, TechnicalDebt


class QualityAssessor:
    """质量评估器"""

    def __init__(self, components: List[CodeComponent], base_path: str = ""):
        self.components = components
        self.technical_debts: List[TechnicalDebt] = []
        self.base_path = Path(base_path)

    def assess_quality(self) -> Dict[str, Any]:
        """评估代码质量"""
        self._assess_technical_debt()

        return {
            "technical_debts": [self._debt_to_dict(d) for d in self.technical_debts],
            "reusability_recommendations": self._generate_reusability_recommendations(),
            "complexity_analysis": self._analyze_complexity(),
        }

    def _assess_technical_debt(self):
        """评估技术债务"""
        for component in self.components:
            # 检查复杂度
            if component.complexity_score == 3:
                self.technical_debts.append(
                    TechnicalDebt(
                        file_path=component.file_path,
                        issue_type="complexity",
                        description=f"{component.name} 的复杂度过高",
                        severity="high",
                        effort_to_fix="large",
                        impact_on_requirements="可能影响需求的实现难度和质量",
                    )
                )

            # 检查可复用性
            if component.reusability_score < 0.5:
                self.technical_debts.append(
                    TechnicalDebt(
                        file_path=component.file_path,
                        issue_type="code_smell",
                        description=f"{component.name} 的可复用性较低",
                        severity="medium",
                        effort_to_fix="medium",
                        impact_on_requirements="可能导致重复代码和维护困难",
                    )
                )

            # 检查依赖数量
            if len(component.dependencies) > 10:
                self.technical_debts.append(
                    TechnicalDebt(
                        file_path=component.file_path,
                        issue_type="dependency",
                        description=f"{component.name} 的依赖过多",
                        severity="medium",
                        effort_to_fix="large",
                        impact_on_requirements="可能增加系统的耦合度和维护难度",
                    )
                )

    def _generate_reusability_recommendations(self) -> List[Dict[str, Any]]:
        """生成可复用性建议"""
        recommendations = []

        for component in self.components:
            if component.reusability_score < 0.8:
                recommendation = {
                    "component": component.name,
                    "current_score": component.reusability_score,
                    "suggestions": [],
                }

                # 根据不同问题提供建议
                if not component.description:
                    recommendation["suggestions"].append(
                        "添加详细的文档字符串，说明组件的功能、参数和返回值"
                    )

                if len(component.dependencies) > 5:
                    recommendation["suggestions"].append("考虑减少依赖数量，提高内聚性")

                if component.complexity_score > 1:
                    recommendation["suggestions"].append(
                        "降低代码复杂度，考虑拆分为更小的函数"
                    )

                recommendations.append(recommendation)

        return recommendations

    def _analyze_complexity(self) -> Dict[str, Any]:
        """分析代码复杂度"""
        analysis = {
            "overall_complexity": 0,
            "complexity_distribution": {
                "simple": 0,  # 复杂度为1
                "medium": 0,  # 复杂度为2
                "complex": 0,  # 复杂度为3
            },
            "hotspots": [],
        }

        total_components = len(self.components)
        if total_components == 0:
            return analysis

        # 统计复杂度分布
        for component in self.components:
            analysis["overall_complexity"] += component.complexity_score

            if component.complexity_score == 1:
                analysis["complexity_distribution"]["simple"] += 1
            elif component.complexity_score == 2:
                analysis["complexity_distribution"]["medium"] += 1
            else:
                analysis["complexity_distribution"]["complex"] += 1

            # 识别复杂度热点
            if component.complexity_score == 3:
                analysis["hotspots"].append(
                    {
                        "name": component.name,
                        "file": component.file_path,
                        "complexity_score": component.complexity_score,
                        "recommendations": [
                            "考虑将复杂的逻辑拆分为多个更小的函数",
                            "使用策略模式或状态模式简化条件逻辑",
                            "添加详细的注释说明复杂逻辑的目的",
                        ],
                    }
                )

        # 计算平均复杂度
        analysis["overall_complexity"] /= total_components

        return analysis

    def _debt_to_dict(self, debt: TechnicalDebt) -> Dict[str, Any]:
        """转换技术债务为字典"""
        return {
            "file_path": debt.file_path,
            "issue_type": debt.issue_type,
            "description": debt.description,
            "severity": debt.severity,
            "effort_to_fix": debt.effort_to_fix,
            "impact_on_requirements": debt.impact_on_requirements,
        }
