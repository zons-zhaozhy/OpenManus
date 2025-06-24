"""
代码库管理器
整合代码库核心功能和分析器，提供统一的管理接口
"""

from typing import Dict, List, Optional

from loguru import logger

from .analyzer import CodeAnalyzer, SimilarityAnalyzer, StructureAnalyzer
from .core import CodebaseCore
from .types import (
    AnalysisResult,
    CodebaseInfo,
    CodeSearchQuery,
    CodeSearchResult,
    SimilarityResult,
    WorkloadEstimation,
)


class CodebaseManager:
    """代码库管理器"""

    def __init__(self, storage_path: str = "data/codebases"):
        """
        初始化代码库管理器

        Args:
            storage_path: 存储路径
        """
        self.core = CodebaseCore(storage_path)
        self.analyzer = CodeAnalyzer()
        self.similarity_analyzer = SimilarityAnalyzer()
        self.structure_analyzer = StructureAnalyzer()

        logger.info("代码库管理器初始化完成")

    # ====== 代码库基本管理 ======

    def create_codebase(
        self,
        name: str,
        description: str,
        root_path: str,
        tags: Optional[List[str]] = None,
        language_primary: Optional[str] = None,
        metadata: Optional[Dict] = None,
        auto_analyze: bool = True,
    ) -> Optional[CodebaseInfo]:
        """
        创建新的代码库

        Args:
            name: 代码库名称
            description: 代码库描述
            root_path: 代码库根路径
            tags: 标签列表
            language_primary: 主要编程语言
            metadata: 元数据
            auto_analyze: 是否自动分析

        Returns:
            CodebaseInfo: 创建的代码库信息
        """
        codebase = self.core.create_codebase(
            name=name,
            description=description,
            root_path=root_path,
            tags=tags,
            language_primary=language_primary,
            metadata=metadata,
        )

        if codebase and auto_analyze:
            logger.info(f"自动分析代码库: {codebase.name}")
            self.analyze_codebase(codebase.id)

        return codebase

    def get_codebase(self, codebase_id: str) -> Optional[CodebaseInfo]:
        """
        获取代码库信息

        Args:
            codebase_id: 代码库ID

        Returns:
            CodebaseInfo: 代码库信息
        """
        return self.core.get_codebase(codebase_id)

    def list_codebases(self, tags: Optional[List[str]] = None) -> List[CodebaseInfo]:
        """
        列出所有代码库

        Args:
            tags: 筛选标签

        Returns:
            List[CodebaseInfo]: 代码库列表
        """
        return self.core.list_codebases(tags)

    def update_codebase(self, codebase_id: str, **updates) -> Optional[CodebaseInfo]:
        """
        更新代码库信息

        Args:
            codebase_id: 代码库ID
            **updates: 更新字段

        Returns:
            CodebaseInfo: 更新后的代码库信息
        """
        return self.core.update_codebase(codebase_id, **updates)

    def delete_codebase(self, codebase_id: str) -> bool:
        """
        删除代码库

        Args:
            codebase_id: 代码库ID

        Returns:
            bool: 删除是否成功
        """
        return self.core.delete_codebase(codebase_id)

    # ====== 代码分析功能 ======

    def analyze_codebase(self, codebase_id: str) -> Optional[AnalysisResult]:
        """
        分析代码库

        Args:
            codebase_id: 代码库ID

        Returns:
            AnalysisResult: 分析结果
        """
        codebase = self.core.get_codebase(codebase_id)
        if not codebase:
            logger.error(f"代码库不存在: {codebase_id}")
            return None

        try:
            # 执行代码分析
            result = self.analyzer.analyze_codebase(codebase_id, codebase.root_path)

            # 添加相似度分析
            similarities = self.similarity_analyzer.analyze_similarity(
                codebase.root_path
            )
            result.similarities = similarities

            # 保存分析结果
            self.core.save_analysis_result(codebase_id, result)

            logger.info(f"代码库分析完成: {codebase.name}")
            return result

        except Exception as e:
            logger.error(f"代码库分析失败: {e}")
            return None

    def get_analysis_result(self, codebase_id: str) -> Optional[AnalysisResult]:
        """
        获取分析结果

        Args:
            codebase_id: 代码库ID

        Returns:
            AnalysisResult: 分析结果
        """
        return self.core.load_analysis_result(codebase_id)

    def analyze_structure(self, codebase_id: str) -> Optional[Dict]:
        """
        分析代码结构

        Args:
            codebase_id: 代码库ID

        Returns:
            Dict: 结构分析结果
        """
        codebase = self.core.get_codebase(codebase_id)
        if not codebase:
            return None

        try:
            components, metrics, languages = self.structure_analyzer.analyze_structure(
                codebase.root_path
            )

            return {
                "components": [
                    {
                        "name": comp.name,
                        "type": comp.type.value,
                        "file_path": comp.file_path,
                        "complexity": comp.complexity.value,
                        "start_line": comp.start_line,
                        "end_line": comp.end_line,
                    }
                    for comp in components
                ],
                "metrics": {
                    "lines_of_code": metrics.lines_of_code,
                    "lines_of_comments": metrics.lines_of_comments,
                    "cyclomatic_complexity": metrics.cyclomatic_complexity,
                    "maintainability_index": metrics.maintainability_index,
                },
                "languages": languages,
            }

        except Exception as e:
            logger.error(f"结构分析失败: {e}")
            return None

    def analyze_similarity(self, codebase_id: str) -> List[SimilarityResult]:
        """
        分析代码相似度

        Args:
            codebase_id: 代码库ID

        Returns:
            List[SimilarityResult]: 相似度结果
        """
        codebase = self.core.get_codebase(codebase_id)
        if not codebase:
            return []

        try:
            return self.similarity_analyzer.analyze_similarity(codebase.root_path)
        except Exception as e:
            logger.error(f"相似度分析失败: {e}")
            return []

    # ====== 搜索功能 ======

    def search_components(self, query: CodeSearchQuery) -> List[CodeSearchResult]:
        """
        搜索代码组件

        Args:
            query: 搜索查询

        Returns:
            List[CodeSearchResult]: 搜索结果
        """
        results = []

        for codebase_id in query.codebase_ids:
            codebase = self.core.get_codebase(codebase_id)
            if not codebase:
                continue

            # 获取分析结果
            analysis = self.get_analysis_result(codebase_id)
            if not analysis:
                continue

            # 搜索组件
            for component in analysis.components:
                # 名称匹配
                if query.query_text.lower() in component.name.lower():
                    relevance_score = 1.0
                # 类型匹配
                elif query.component_types and component.type in query.component_types:
                    relevance_score = 0.8
                # 文件路径匹配
                elif any(
                    pattern in component.file_path for pattern in query.file_patterns
                ):
                    relevance_score = 0.6
                else:
                    continue

                # 排除模式
                if any(
                    pattern in component.file_path for pattern in query.exclude_patterns
                ):
                    continue

                results.append(
                    CodeSearchResult(
                        component=component,
                        codebase_id=codebase_id,
                        relevance_score=relevance_score,
                        content_snippet=f"{component.name} in {component.file_path}",
                    )
                )

        # 按相关性排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        # 限制结果数量
        return results[: query.max_results]

    # ====== 工作量估算 ======

    def estimate_workload(
        self, codebase_id: str, task_description: str = ""
    ) -> Optional[WorkloadEstimation]:
        """
        估算工作量

        Args:
            codebase_id: 代码库ID
            task_description: 任务描述

        Returns:
            WorkloadEstimation: 工作量估算结果
        """
        analysis = self.get_analysis_result(codebase_id)
        if not analysis:
            return None

        try:
            # 基础估算（基于现有代码）
            base_days = analysis.estimated_effort_days

            # 根据任务调整
            adjustment_factor = 1.0
            if "重构" in task_description:
                adjustment_factor = 0.7  # 重构相对容易
            elif "新功能" in task_description:
                adjustment_factor = 1.2  # 新功能需要更多时间
            elif "优化" in task_description:
                adjustment_factor = 0.8  # 优化相对简单

            estimated_days = base_days * adjustment_factor

            # 分解估算
            breakdown = {
                "需求分析": estimated_days * 0.15,
                "设计": estimated_days * 0.20,
                "编码": estimated_days * 0.40,
                "测试": estimated_days * 0.20,
                "部署": estimated_days * 0.05,
            }

            # 置信度计算
            confidence = 0.8  # 基础置信度
            if analysis.metrics.maintainability_index > 80:
                confidence += 0.1
            if len(analysis.tech_stacks) > 5:
                confidence -= 0.1  # 技术栈复杂度影响
            confidence = max(0.1, min(1.0, confidence))

            # 风险和假设
            assumptions = [
                "开发团队具备相应技术栈经验",
                "需求相对稳定，变更较少",
                "具备完整的开发环境和工具",
            ]

            risks = []
            if analysis.metrics.cyclomatic_complexity > 50:
                risks.append("代码复杂度较高，可能影响开发效率")
            if len(analysis.similarities) > 10:
                risks.append("存在较多重复代码，需要重构")
            if not any(ts.type.value == "testing" for ts in analysis.tech_stacks):
                risks.append("缺乏测试框架，测试阶段可能延长")

            return WorkloadEstimation(
                total_days=round(estimated_days, 1),
                breakdown=breakdown,
                confidence=confidence,
                assumptions=assumptions,
                risks=risks,
            )

        except Exception as e:
            logger.error(f"工作量估算失败: {e}")
            return None

    # ====== 统计信息 ======

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        base_stats = self.core.get_statistics()

        # 添加分析统计
        analyzed_count = 0
        total_components = 0
        total_similarities = 0

        for codebase in self.list_codebases():
            analysis = self.get_analysis_result(codebase.id)
            if analysis:
                analyzed_count += 1
                total_components += len(analysis.components)
                total_similarities += len(analysis.similarities)

        # 将组件统计添加到顶级字典
        return {
            **base_stats,
            "total_components": total_components,  # 添加到顶级
            "total_similarities": total_similarities,  # 添加到顶级
            "analysis_stats": {
                "analyzed_codebases": analyzed_count,
                "total_components": total_components,
                "total_similarities": total_similarities,
                "analysis_coverage": round(
                    analyzed_count / max(base_stats["total_codebases"], 1) * 100, 1
                ),
            },
        }

    def get_tech_stack_distribution(self) -> Dict[str, int]:
        """
        获取技术栈分布统计

        Returns:
            Dict: 技术栈分布
        """
        tech_stack_count = {}

        for codebase in self.list_codebases():
            analysis = self.get_analysis_result(codebase.id)
            if analysis:
                for tech_stack in analysis.tech_stacks:
                    name = tech_stack.name
                    tech_stack_count[name] = tech_stack_count.get(name, 0) + 1

        return tech_stack_count

    def get_complexity_distribution(self) -> Dict[str, int]:
        """
        获取复杂度分布统计

        Returns:
            Dict: 复杂度分布
        """
        complexity_count = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "very_high": 0,
        }

        for codebase in self.list_codebases():
            analysis = self.get_analysis_result(codebase.id)
            if analysis:
                for component in analysis.components:
                    complexity_count[component.complexity.value] += 1

        return complexity_count
