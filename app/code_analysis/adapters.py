"""
代码分析适配器 - 为增强版代码分析提供兼容性接口
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.modules.codebase.analyzer import CodeAnalyzer as EnhancedCodeAnalyzer
from app.modules.codebase.types import AnalysisResult, ComponentType

from .models.base import CodeComponent, CodePattern, TechnicalDebt


class EnhancedCodeAnalyzerAdapter:
    """增强版代码分析适配器 - 提供与旧版代码分析兼容的接口"""

    def __init__(self, project_root: str = None):
        self.analyzer = EnhancedCodeAnalyzer()
        self.project_root = project_root
        self.analysis_cache: Dict[str, Any] = {}

    def analyze(self, target_dirs: List[str] = None) -> Dict[str, Any]:
        """
        分析代码 - 同步版本

        Args:
            target_dirs: 目标目录列表

        Returns:
            Dict[str, Any]: 分析结果
        """
        return self.analyze_codebase(target_dirs)

    async def analyze_async(self, target_dirs: List[str] = None) -> Dict[str, Any]:
        """
        分析代码 - 异步版本

        Args:
            target_dirs: 目标目录列表

        Returns:
            Dict[str, Any]: 分析结果
        """
        return self.analyze_codebase(target_dirs)

    def analyze_codebase(self, target_dirs: List[str] = None) -> Dict[str, Any]:
        """分析代码库"""
        try:
            if target_dirs is None:
                target_dirs = ["app/", "src/", "lib/"]

            # 使用增强版分析器
            result = self.analyzer.analyze_codebase(
                codebase_id="temp",  # 临时ID
                root_path=self.project_root or ".",
            )

            # 缓存结果
            self.analysis_cache = {
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }

            # 转换结果格式
            analysis_result = {
                "project_overview": {
                    "total_files": result.file_count,
                    "languages": result.languages,
                },
                "components": [],
                "patterns": [],
                "technical_debts": [],
                "reusability_recommendations": [],
                "complexity_analysis": {},
            }

            # 转换组件
            for comp in result.components:
                # 检查组件是否在目标目录中
                if target_dirs and not any(
                    comp.file_path.startswith(dir_path) for dir_path in target_dirs
                ):
                    continue

                analysis_result["components"].append(
                    CodeComponent(
                        name=comp.name,
                        type=(
                            comp.type.value
                            if hasattr(comp.type, "value")
                            else comp.type
                        ),
                        file_path=comp.file_path,
                        line_start=comp.start_line,
                        line_end=comp.end_line,
                        description=(
                            comp.description if hasattr(comp, "description") else ""
                        ),
                        dependencies=(
                            comp.dependencies if hasattr(comp, "dependencies") else []
                        ),
                        complexity_score=(
                            comp.complexity.value
                            if hasattr(comp.complexity, "value")
                            else 1
                        ),
                        reusability_score=result.reusability_score,
                    )
                )

            # 转换技术债务
            for issue in result.quality_issues:
                # 检查问题是否在目标目录中
                if target_dirs and not any(
                    issue.file_path.startswith(dir_path) for dir_path in target_dirs
                ):
                    continue

                analysis_result["technical_debts"].append(
                    TechnicalDebt(
                        name=issue.title,
                        description=issue.description,
                        severity=issue.severity,
                        file_path=issue.file_path,
                        line_number=(
                            issue.line_number if hasattr(issue, "line_number") else 0
                        ),
                        recommendations=(
                            issue.recommendations
                            if hasattr(issue, "recommendations")
                            else []
                        ),
                    )
                )

            # 添加建议
            analysis_result["reusability_recommendations"] = result.suggestions

            # 添加复杂度分析
            analysis_result["complexity_analysis"] = {
                "overall_complexity": result.metrics.cyclomatic_complexity,
                "maintainability_index": result.metrics.maintainability_index,
            }

            return analysis_result

        except Exception as e:
            logger.error(f"代码分析失败: {e}")
            return {
                "project_overview": {"total_files": 0, "languages": {}},
                "components": [],
                "patterns": [],
                "technical_debts": [],
                "reusability_recommendations": [],
                "complexity_analysis": {},
                "error": str(e),
            }

    def analyze_class(self, node: Any, file_path: str, content: str) -> CodeComponent:
        """分析类定义 - 兼容性方法"""
        # 由于增强版使用不同的分析方式，这里提供一个简化的实现
        return CodeComponent(
            name=node.name if hasattr(node, "name") else "Unknown",
            type="class",
            file_path=file_path,
            line_start=getattr(node, "lineno", 0),
            line_end=getattr(node, "end_lineno", 0),
            description="",
            dependencies=[],
            complexity_score=1,
            reusability_score=0.7,
        )

    def analyze_function(
        self, node: Any, file_path: str, content: str
    ) -> CodeComponent:
        """分析函数定义 - 兼容性方法"""
        # 由于增强版使用不同的分析方式，这里提供一个简化的实现
        return CodeComponent(
            name=node.name if hasattr(node, "name") else "Unknown",
            type="function",
            file_path=file_path,
            line_start=getattr(node, "lineno", 0),
            line_end=getattr(node, "end_lineno", 0),
            description="",
            dependencies=[],
            complexity_score=1,
            reusability_score=0.7,
        )
