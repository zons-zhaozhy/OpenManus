"""
自适应学习系统 - 需求分析助手的自我学习和进化能力

基于最新的AI技术趋势，实现：
1. 反馈学习机制：从用户反馈中学习
2. 模式识别优化：不断优化需求模式识别
3. 质量评估改进：基于历史数据改进质量评估标准
4. 知识库自动更新：积累和更新需求分析知识
"""

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.logger import logger


@dataclass
class AnalysisCase:
    """需求分析案例"""

    case_id: str
    user_input: str
    initial_analysis: dict
    clarification_questions: List[dict]
    user_answers: List[dict]
    final_quality: float
    user_satisfaction: float
    completion_time: float
    success_indicators: dict
    timestamp: datetime

    def to_dict(self) -> dict:
        """转换为字典格式"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisCase":
        """从字典创建实例"""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class LearningInsight:
    """学习洞察"""

    insight_type: str  # pattern, quality_factor, optimization
    description: str
    confidence: float
    supporting_cases: List[str]
    actionable_recommendation: str
    impact_score: float


class AdaptiveLearningSystem:
    """自适应学习系统"""

    def __init__(self, knowledge_base_path: str = "data/knowledge_base.db"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.parent.mkdir(exist_ok=True)

        # 初始化数据库
        self._init_database()

        # 学习参数
        self.min_cases_for_learning = 10
        self.learning_confidence_threshold = 0.7
        self.pattern_similarity_threshold = 0.8

        # 模型组件
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
        self.pattern_clusters = None

        logger.info("自适应学习系统初始化完成")

    def _init_database(self):
        """初始化知识库数据库"""
        with sqlite3.connect(self.knowledge_base_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS analysis_cases (
                    case_id TEXT PRIMARY KEY,
                    user_input TEXT NOT NULL,
                    initial_analysis TEXT NOT NULL,
                    clarification_questions TEXT NOT NULL,
                    user_answers TEXT NOT NULL,
                    final_quality REAL NOT NULL,
                    user_satisfaction REAL NOT NULL,
                    completion_time REAL NOT NULL,
                    success_indicators TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS learning_insights (
                    insight_id TEXT PRIMARY KEY,
                    insight_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    supporting_cases TEXT NOT NULL,
                    actionable_recommendation TEXT NOT NULL,
                    impact_score REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pattern_models (
                    model_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    model_data TEXT NOT NULL,
                    performance_metrics TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_cases_timestamp ON analysis_cases(timestamp);
                CREATE INDEX IF NOT EXISTS idx_cases_quality ON analysis_cases(final_quality);
                CREATE INDEX IF NOT EXISTS idx_insights_type ON learning_insights(insight_type);
            """
            )

    def record_analysis_case(self, case: AnalysisCase):
        """记录分析案例"""
        with sqlite3.connect(self.knowledge_base_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analysis_cases
                (case_id, user_input, initial_analysis, clarification_questions,
                 user_answers, final_quality, user_satisfaction, completion_time,
                 success_indicators, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case.case_id,
                    case.user_input,
                    json.dumps(case.initial_analysis),
                    json.dumps(case.clarification_questions),
                    json.dumps(case.user_answers),
                    case.final_quality,
                    case.user_satisfaction,
                    case.completion_time,
                    json.dumps(case.success_indicators),
                    case.timestamp.isoformat(),
                ),
            )

        logger.info(f"记录分析案例: {case.case_id}")

        # 触发学习过程
        self._trigger_learning_if_ready()

    def _trigger_learning_if_ready(self):
        """如果条件满足，触发学习过程"""
        case_count = self._get_total_case_count()

        # 每积累一定数量案例后触发学习
        if case_count >= self.min_cases_for_learning and case_count % 5 == 0:
            logger.info(f"触发自我学习过程，当前案例数量: {case_count}")
            self.perform_self_learning()

    def _get_total_case_count(self) -> int:
        """获取总案例数量"""
        with sqlite3.connect(self.knowledge_base_path) as conn:
            result = conn.execute("SELECT COUNT(*) FROM analysis_cases").fetchone()
            return result[0] if result else 0

    def perform_self_learning(self) -> List[LearningInsight]:
        """执行自我学习"""
        logger.info("开始自我学习过程")

        insights = []

        # 1. 模式识别学习
        pattern_insights = self._learn_requirement_patterns()
        insights.extend(pattern_insights)

        # 2. 质量因子学习
        quality_insights = self._learn_quality_factors()
        insights.extend(quality_insights)

        # 3. 效率优化学习
        efficiency_insights = self._learn_efficiency_optimizations()
        insights.extend(efficiency_insights)

        # 4. 问题策略学习
        question_insights = self._learn_question_strategies()
        insights.extend(question_insights)

        # 保存学习洞察
        self._save_insights(insights)

        logger.info(f"自我学习完成，生成 {len(insights)} 个洞察")
        return insights

    def _learn_requirement_patterns(self) -> List[LearningInsight]:
        """学习需求模式"""
        insights = []

        # 获取近期案例
        cases = self._get_recent_cases(days=30)
        if len(cases) < self.min_cases_for_learning:
            return insights

        # 提取用户输入文本
        user_inputs = [case.user_input for case in cases]

        try:
            # 向量化和聚类
            X = self.vectorizer.fit_transform(user_inputs)
            n_clusters = min(5, len(cases) // 3)  # 动态确定聚类数量

            if n_clusters >= 2:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = kmeans.fit_predict(X)

                # 分析每个聚类
                for cluster_id in range(n_clusters):
                    cluster_cases = [
                        cases[i]
                        for i, label in enumerate(cluster_labels)
                        if label == cluster_id
                    ]

                    if len(cluster_cases) >= 3:  # 聚类需要有足够案例
                        # 分析聚类特征
                        avg_quality = np.mean(
                            [case.final_quality for case in cluster_cases]
                        )
                        avg_satisfaction = np.mean(
                            [case.user_satisfaction for case in cluster_cases]
                        )

                        # 识别成功模式
                        if avg_quality >= 0.8 and avg_satisfaction >= 0.8:
                            insight = LearningInsight(
                                insight_type="successful_pattern",
                                description=f"识别到高成功率需求模式，集群包含{len(cluster_cases)}个案例",
                                confidence=min(
                                    avg_quality + avg_satisfaction - 1.0, 1.0
                                ),
                                supporting_cases=[
                                    case.case_id for case in cluster_cases
                                ],
                                actionable_recommendation="对此类需求模式，可以优化初始分析策略",
                                impact_score=len(cluster_cases) / len(cases),
                            )
                            insights.append(insight)

                        # 识别问题模式
                        elif avg_quality < 0.6 or avg_satisfaction < 0.6:
                            insight = LearningInsight(
                                insight_type="problematic_pattern",
                                description=f"识别到低成功率需求模式，需要改进策略",
                                confidence=max(
                                    1.0 - avg_quality, 1.0 - avg_satisfaction
                                ),
                                supporting_cases=[
                                    case.case_id for case in cluster_cases
                                ],
                                actionable_recommendation="对此类需求模式，需要增强澄清策略",
                                impact_score=len(cluster_cases) / len(cases),
                            )
                            insights.append(insight)

        except Exception as e:
            logger.error(f"模式学习出错: {e}")

        return insights

    def _learn_quality_factors(self) -> List[LearningInsight]:
        """学习影响质量的因子"""
        insights = []

        cases = self._get_recent_cases(days=60)
        if len(cases) < self.min_cases_for_learning:
            return insights

        # 分析质量影响因子
        high_quality_cases = [case for case in cases if case.final_quality >= 0.8]
        low_quality_cases = [case for case in cases if case.final_quality < 0.6]

        if len(high_quality_cases) >= 3 and len(low_quality_cases) >= 3:
            # 分析澄清问题数量的影响
            high_q_avg_questions = np.mean(
                [len(case.clarification_questions) for case in high_quality_cases]
            )
            low_q_avg_questions = np.mean(
                [len(case.clarification_questions) for case in low_quality_cases]
            )

            if abs(high_q_avg_questions - low_q_avg_questions) > 1.0:
                insight = LearningInsight(
                    insight_type="quality_factor",
                    description=f"澄清问题数量与质量相关：高质量案例平均{high_q_avg_questions:.1f}个问题，低质量案例平均{low_q_avg_questions:.1f}个问题",
                    confidence=0.8,
                    supporting_cases=[
                        case.case_id for case in high_quality_cases + low_quality_cases
                    ],
                    actionable_recommendation=f"建议优化澄清问题数量到{high_q_avg_questions:.0f}个左右",
                    impact_score=0.7,
                )
                insights.append(insight)

            # 分析完成时间的影响
            high_q_avg_time = np.mean(
                [case.completion_time for case in high_quality_cases]
            )
            low_q_avg_time = np.mean(
                [case.completion_time for case in low_quality_cases]
            )

            if abs(high_q_avg_time - low_q_avg_time) > 30:  # 30秒差异
                insight = LearningInsight(
                    insight_type="quality_factor",
                    description=f"分析时间与质量相关：高质量案例平均{high_q_avg_time:.0f}秒，低质量案例平均{low_q_avg_time:.0f}秒",
                    confidence=0.7,
                    supporting_cases=[
                        case.case_id for case in high_quality_cases + low_quality_cases
                    ],
                    actionable_recommendation="建议调整分析时间分配策略",
                    impact_score=0.6,
                )
                insights.append(insight)

        return insights

    def _learn_efficiency_optimizations(self) -> List[LearningInsight]:
        """学习效率优化策略"""
        insights = []

        cases = self._get_recent_cases(days=45)
        if len(cases) < self.min_cases_for_learning:
            return insights

        # 分析效率指标
        efficiency_scores = []
        for case in cases:
            # 效率 = 质量 / 时间 * 100
            if case.completion_time > 0:
                efficiency = (case.final_quality / case.completion_time) * 100
                efficiency_scores.append((case, efficiency))

        if efficiency_scores:
            # 排序找出最高效的案例
            efficiency_scores.sort(key=lambda x: x[1], reverse=True)
            top_efficient = efficiency_scores[
                : len(efficiency_scores) // 3
            ]  # 前1/3最高效

            if len(top_efficient) >= 3:
                avg_questions = np.mean(
                    [len(case.clarification_questions) for case, _ in top_efficient]
                )
                avg_time = np.mean([case.completion_time for case, _ in top_efficient])

                insight = LearningInsight(
                    insight_type="efficiency_optimization",
                    description=f"高效案例特征：平均{avg_questions:.1f}个问题，{avg_time:.0f}秒完成",
                    confidence=0.8,
                    supporting_cases=[case.case_id for case, _ in top_efficient],
                    actionable_recommendation="建议采用高效案例的问题数量和时间分配策略",
                    impact_score=0.8,
                )
                insights.append(insight)

        return insights

    def _learn_question_strategies(self) -> List[LearningInsight]:
        """学习问题策略"""
        insights = []

        cases = self._get_recent_cases(days=30)
        if len(cases) < self.min_cases_for_learning:
            return insights

        # 分析不同类型问题的效果
        question_categories = {}

        for case in cases:
            for question in case.clarification_questions:
                category = question.get("category", "unknown")
                if category not in question_categories:
                    question_categories[category] = []
                question_categories[category].append(case.final_quality)

        # 找出最有效的问题类型
        effective_categories = []
        for category, qualities in question_categories.items():
            if len(qualities) >= 3:
                avg_quality = np.mean(qualities)
                if avg_quality >= 0.75:
                    effective_categories.append((category, avg_quality, len(qualities)))

        if effective_categories:
            effective_categories.sort(key=lambda x: x[1], reverse=True)
            top_category = effective_categories[0]

            insight = LearningInsight(
                insight_type="question_strategy",
                description=f"最有效的问题类型：{top_category[0]}，平均质量{top_category[1]:.2f}",
                confidence=0.8,
                supporting_cases=[],  # 简化处理
                actionable_recommendation=f"建议增加{top_category[0]}类型问题的比例",
                impact_score=top_category[2] / len(cases),
            )
            insights.append(insight)

        return insights

    def _get_recent_cases(self, days: int = 30) -> List[AnalysisCase]:
        """获取最近的案例"""
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.knowledge_base_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM analysis_cases
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (cutoff_date.isoformat(),),
            )

            cases = []
            for row in cursor.fetchall():
                case_data = {
                    "case_id": row[0],
                    "user_input": row[1],
                    "initial_analysis": json.loads(row[2]),
                    "clarification_questions": json.loads(row[3]),
                    "user_answers": json.loads(row[4]),
                    "final_quality": row[5],
                    "user_satisfaction": row[6],
                    "completion_time": row[7],
                    "success_indicators": json.loads(row[8]),
                    "timestamp": datetime.fromisoformat(row[9]),
                }
                cases.append(AnalysisCase.from_dict(case_data))

            return cases

    def _save_insights(self, insights: List[LearningInsight]):
        """保存学习洞察"""
        if not insights:
            return

        with sqlite3.connect(self.knowledge_base_path) as conn:
            for insight in insights:
                insight_id = f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{insight.insight_type}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO learning_insights
                    (insight_id, insight_type, description, confidence,
                     supporting_cases, actionable_recommendation, impact_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        insight_id,
                        insight.insight_type,
                        insight.description,
                        insight.confidence,
                        json.dumps(insight.supporting_cases),
                        insight.actionable_recommendation,
                        insight.impact_score,
                        datetime.now().isoformat(),
                    ),
                )

    def get_actionable_recommendations(self, limit: int = 5) -> List[LearningInsight]:
        """获取可操作的建议"""
        with sqlite3.connect(self.knowledge_base_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM learning_insights
                WHERE confidence >= ?
                ORDER BY impact_score DESC, confidence DESC
                LIMIT ?
            """,
                (self.learning_confidence_threshold, limit),
            )

            recommendations = []
            for row in cursor.fetchall():
                insight = LearningInsight(
                    insight_type=row[1],
                    description=row[2],
                    confidence=row[3],
                    supporting_cases=json.loads(row[4]),
                    actionable_recommendation=row[5],
                    impact_score=row[6],
                )
                recommendations.append(insight)

            return recommendations

    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        with sqlite3.connect(self.knowledge_base_path) as conn:
            # 案例统计
            case_stats = conn.execute(
                """
                SELECT
                    COUNT(*) as total_cases,
                    AVG(final_quality) as avg_quality,
                    AVG(user_satisfaction) as avg_satisfaction,
                    AVG(completion_time) as avg_time
                FROM analysis_cases
            """
            ).fetchone()

            # 洞察统计
            insight_stats = conn.execute(
                """
                SELECT
                    insight_type,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence,
                    AVG(impact_score) as avg_impact
                FROM learning_insights
                GROUP BY insight_type
            """
            ).fetchall()

            return {
                "total_cases": case_stats[0] if case_stats else 0,
                "average_quality": case_stats[1] if case_stats else 0.0,
                "average_satisfaction": case_stats[2] if case_stats else 0.0,
                "average_completion_time": case_stats[3] if case_stats else 0.0,
                "insights_by_type": {
                    row[0]: {
                        "count": row[1],
                        "avg_confidence": row[2],
                        "avg_impact": row[3],
                    }
                    for row in insight_stats
                },
                "total_insights": sum(row[1] for row in insight_stats),
                "learning_maturity": self._calculate_learning_maturity(),
            }

    def _calculate_learning_maturity(self) -> float:
        """计算学习成熟度"""
        case_count = self._get_total_case_count()

        # 基于案例数量和洞察质量计算成熟度
        if case_count == 0:
            return 0.0

        # 案例数量贡献 (0-0.4)
        case_maturity = min(case_count / 100, 0.4)

        # 洞察质量贡献 (0-0.6)
        recommendations = self.get_actionable_recommendations(limit=10)
        if recommendations:
            avg_confidence = np.mean([r.confidence for r in recommendations])
            avg_impact = np.mean([r.impact_score for r in recommendations])
            insight_maturity = (avg_confidence + avg_impact) / 2 * 0.6
        else:
            insight_maturity = 0.0

        return case_maturity + insight_maturity


# 全局实例
adaptive_learning_system = AdaptiveLearningSystem()
