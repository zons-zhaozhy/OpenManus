"""
增强版需求分析引擎
基于多维度分析，增加记忆、学习和优化能力

新增功能：
1. 历史分析记忆和学习
2. 模板化加速分析
3. 智能缓存机制
4. 持续优化算法
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import Config
from app.core.multi_dimensional_engine import (
    DimensionResult,
    MultiDimensionalAnalysisEngine,
)
from app.llm import LLM
from app.logger import logger


@dataclass
class AnalysisTemplate:
    """分析模板"""

    domain: str  # 业务域
    template_data: Dict[str, Any]  # 模板数据
    usage_count: int = 0  # 使用次数
    success_rate: float = 0.0  # 成功率
    avg_quality_score: float = 0.0  # 平均质量评分


@dataclass
class HistoricalAnalysis:
    """历史分析记录"""

    session_id: str
    original_content: str
    analysis_result: Dict[str, Any]
    quality_score: float
    user_feedback: Optional[str] = None
    timestamp: float = 0


class EnhancedRequirementsEngine(MultiDimensionalAnalysisEngine):
    """增强版需求分析引擎"""

    def __init__(self):
        super().__init__()

        # 历史数据存储
        self.data_dir = Path("data/requirements_analysis")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 分析模板库
        self.templates: Dict[str, AnalysisTemplate] = {}
        self.load_templates()

        # 历史分析记录
        self.historical_analyses: List[HistoricalAnalysis] = []
        self.load_historical_data()

        # 性能缓存
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"增强版分析引擎初始化完成，已加载 {len(self.templates)} 个模板，{len(self.historical_analyses)} 条历史记录"
        )

    async def analyze_requirement_enhanced(
        self,
        content: str,
        project_context: Optional[Dict] = None,
        use_templates: bool = True,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """增强版需求分析"""
        start_time = time.time()
        logger.info(f"开始增强版需求分析，内容: {content[:50]}...")

        try:
            # 1. 缓存检查
            if use_cache:
                cached_result = self._check_cache(content)
                if cached_result:
                    logger.info("命中分析缓存，直接返回结果")
                    return cached_result

            # 2. 模板匹配
            matched_template = None
            if use_templates:
                matched_template = await self._match_template(content)
                if matched_template:
                    logger.info(f"匹配到模板: {matched_template.domain}")

            # 3. 智能预处理
            preprocessed_content = await self._preprocess_with_history(content)

            # 4. 执行多维度分析（使用模板加速）
            if matched_template:
                analysis_result = await self._template_accelerated_analysis(
                    preprocessed_content, project_context, matched_template
                )
            else:
                analysis_result = await super().analyze_requirement(
                    preprocessed_content, project_context
                )

            # 5. 后处理优化
            enhanced_result = await self._enhance_result_with_learning(
                content, analysis_result
            )

            # 6. 更新缓存和学习数据
            if use_cache:
                self._update_cache(content, enhanced_result)

            await self._learn_from_analysis(content, enhanced_result)

            total_time = time.time() - start_time
            logger.info(f"增强版分析完成，总耗时: {total_time:.2f}秒")

            return enhanced_result

        except Exception as e:
            logger.error(f"增强版分析失败: {e}")
            # 降级到基础分析
            logger.info("降级到基础多维度分析")
            return await super().analyze_requirement(content, project_context)

    def _check_cache(self, content: str) -> Optional[Dict[str, Any]]:
        """检查分析缓存"""
        content_hash = hash(content)
        return self.analysis_cache.get(str(content_hash))

    def _update_cache(self, content: str, result: Dict[str, Any]):
        """更新分析缓存"""
        content_hash = hash(content)
        self.analysis_cache[str(content_hash)] = result

        # 缓存大小控制
        if len(self.analysis_cache) > 100:
            # 删除最旧的缓存项
            oldest_key = min(self.analysis_cache.keys())
            del self.analysis_cache[oldest_key]

    async def _match_template(self, content: str) -> Optional[AnalysisTemplate]:
        """智能模板匹配"""
        if not self.templates:
            return None

        # 使用LLM进行语义匹配
        domains = list(self.templates.keys())
        prompt = f"""请分析以下需求属于哪个业务域：

需求内容："{content}"

可选业务域：{domains}

请返回最匹配的业务域名称，如果都不匹配请返回"无匹配"。
只返回业务域名称，不要其他内容。"""

        try:
            response = await self.llm.ask(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                stream=False,
            )

            matched_domain = response.strip()
            if matched_domain in self.templates:
                template = self.templates[matched_domain]
                template.usage_count += 1
                return template

        except Exception as e:
            logger.warning(f"模板匹配失败: {e}")

        return None

    async def _preprocess_with_history(self, content: str) -> str:
        """基于历史数据预处理内容"""
        if not self.historical_analyses:
            return content

        # 寻找相似的历史分析
        similar_analyses = []
        for analysis in self.historical_analyses[-10:]:  # 只看最近10个
            if self._calculate_similarity(content, analysis.original_content) > 0.7:
                similar_analyses.append(analysis)

        if similar_analyses:
            # 添加历史上下文
            context_info = (
                f"\n\n[历史参考：基于{len(similar_analyses)}个相似需求的分析经验]"
            )
            return content + context_info

        return content

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0

    async def _template_accelerated_analysis(
        self, content: str, project_context: Optional[Dict], template: AnalysisTemplate
    ) -> Dict[str, Any]:
        """使用模板加速分析"""
        logger.info(f"使用模板加速分析，模板域: {template.domain}")

        # 基础分析（可以部分使用模板数据）
        base_result = await super().analyze_requirement(content, project_context)

        # 模板增强
        template_enhancements = template.template_data.get("enhancements", {})

        # 合并模板建议
        if "common_risks" in template_enhancements:
            base_result.setdefault("template_risks", []).extend(
                template_enhancements["common_risks"]
            )

        if "best_practices" in template_enhancements:
            base_result.setdefault("template_best_practices", []).extend(
                template_enhancements["best_practices"]
            )

        base_result["used_template"] = template.domain
        base_result["template_confidence"] = template.success_rate

        return base_result

    async def _enhance_result_with_learning(
        self, content: str, analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于学习数据增强结果"""

        # 添加学习增强字段
        analysis_result["learning_enhancements"] = {
            "historical_insights": self._get_historical_insights(content),
            "pattern_recognition": self._recognize_patterns(content),
            "optimization_suggestions": self._get_optimization_suggestions(
                analysis_result
            ),
        }

        return analysis_result

    def _get_historical_insights(self, content: str) -> List[str]:
        """获取历史洞察"""
        insights = []

        # 基于历史高质量分析提取洞察
        high_quality_analyses = [
            a for a in self.historical_analyses if a.quality_score > 85
        ]

        if high_quality_analyses:
            insights.append(f"基于{len(high_quality_analyses)}个高质量历史分析的经验")

        return insights

    def _recognize_patterns(self, content: str) -> List[str]:
        """识别需求模式"""
        patterns = []

        # 简单的模式识别
        if "聊天机器人" in content or "AI" in content:
            patterns.append("AI/ML项目模式")
        if "平台" in content:
            patterns.append("平台型产品模式")
        if "系统" in content:
            patterns.append("系统级开发模式")

        return patterns

    def _get_optimization_suggestions(
        self, analysis_result: Dict[str, Any]
    ) -> List[str]:
        """获取优化建议"""
        suggestions = []

        quality_score = analysis_result.get("quality_score", 0)
        if quality_score < 80:
            suggestions.append("建议补充更详细的需求描述以提升分析质量")

        conflicts = analysis_result.get("conflicts_detected", [])
        if len(conflicts) > 3:
            suggestions.append("检测到较多冲突，建议优先解决高优先级冲突")

        return suggestions

    async def _learn_from_analysis(self, content: str, result: Dict[str, Any]):
        """从分析中学习"""

        # 记录历史分析
        analysis_record = HistoricalAnalysis(
            session_id=result.get("session_id", "unknown"),
            original_content=content,
            analysis_result=result,
            quality_score=result.get("quality_score", 0),
            timestamp=time.time(),
        )

        self.historical_analyses.append(analysis_record)

        # 限制历史记录数量
        if len(self.historical_analyses) > 1000:
            self.historical_analyses = self.historical_analyses[-500:]

        # 更新模板（如果使用了模板）
        if "used_template" in result:
            template_domain = result["used_template"]
            if template_domain in self.templates:
                template = self.templates[template_domain]
                template.avg_quality_score = (
                    template.avg_quality_score * (template.usage_count - 1)
                    + result.get("quality_score", 0)
                ) / template.usage_count

        # 定期保存数据
        if len(self.historical_analyses) % 10 == 0:
            self.save_historical_data()

    def load_templates(self):
        """加载分析模板"""
        template_file = self.data_dir / "analysis_templates.json"

        if template_file.exists():
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for domain, template_data in data.items():
                        self.templates[domain] = AnalysisTemplate(**template_data)
                logger.info(f"加载了 {len(self.templates)} 个分析模板")
            except Exception as e:
                logger.warning(f"加载模板失败: {e}")
        else:
            # 创建默认模板
            self._create_default_templates()

    def _create_default_templates(self):
        """创建默认模板"""
        default_templates = {
            "AI/机器学习": AnalysisTemplate(
                domain="AI/机器学习",
                template_data={
                    "enhancements": {
                        "common_risks": [
                            "数据质量和标注成本风险",
                            "模型训练时间和计算资源风险",
                            "AI模型可解释性和合规风险",
                        ],
                        "best_practices": [
                            "优先使用预训练模型进行微调",
                            "建立完善的数据管道和版本控制",
                            "实施A/B测试验证模型效果",
                        ],
                    }
                },
            ),
            "在线平台": AnalysisTemplate(
                domain="在线平台",
                template_data={
                    "enhancements": {
                        "common_risks": [
                            "高并发和系统可扩展性风险",
                            "用户数据安全和隐私合规风险",
                            "支付系统集成和交易安全风险",
                        ],
                        "best_practices": [
                            "采用微服务架构和云原生部署",
                            "实施多层次的安全防护机制",
                            "建立完善的监控和告警体系",
                        ],
                    }
                },
            ),
        }

        self.templates.update(default_templates)
        self.save_templates()

    def save_templates(self):
        """保存分析模板"""
        template_file = self.data_dir / "analysis_templates.json"

        try:
            data = {
                domain: asdict(template) for domain, template in self.templates.items()
            }
            with open(template_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存模板失败: {e}")

    def load_historical_data(self):
        """加载历史数据"""
        history_file = self.data_dir / "historical_analyses.json"

        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.historical_analyses = [
                        HistoricalAnalysis(**item) for item in data
                    ]
                logger.info(f"加载了 {len(self.historical_analyses)} 条历史分析记录")
            except Exception as e:
                logger.warning(f"加载历史数据失败: {e}")

    def save_historical_data(self):
        """保存历史数据"""
        history_file = self.data_dir / "historical_analyses.json"

        try:
            data = [asdict(analysis) for analysis in self.historical_analyses]
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史数据失败: {e}")

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """获取分析统计数据"""
        return {
            "total_analyses": len(self.historical_analyses),
            "templates_count": len(self.templates),
            "cache_size": len(self.analysis_cache),
            "average_quality_score": (
                (
                    sum(a.quality_score for a in self.historical_analyses)
                    / len(self.historical_analyses)
                )
                if self.historical_analyses
                else 0
            ),
            "template_usage": {
                domain: template.usage_count
                for domain, template in self.templates.items()
            },
        }
