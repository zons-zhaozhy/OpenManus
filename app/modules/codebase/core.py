"""
代码库核心功能模块
提供代码库的基础功能和数据管理
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from .types import AnalysisResult, CodebaseInfo


class CodebaseCore:
    """代码库核心管理器"""

    def __init__(self, storage_path: str = "data/codebases"):
        """
        初始化代码库核心管理器

        Args:
            storage_path: 存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 代码库数据存储路径
        self.codebases_file = self.storage_path / "codebases.json"
        self.analysis_results_dir = self.storage_path / "analysis_results"
        self.analysis_results_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._codebases: Dict[str, CodebaseInfo] = {}
        self._load_codebases()

        logger.info(f"代码库核心管理器初始化完成，存储路径: {self.storage_path}")

    def _load_codebases(self):
        """加载代码库数据"""
        try:
            if self.codebases_file.exists():
                import json

                with open(self.codebases_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for codebase_data in data.get("codebases", []):
                    codebase = self._dict_to_codebase(codebase_data)
                    self._codebases[codebase.id] = codebase

                logger.info(f"已加载 {len(self._codebases)} 个代码库")
        except Exception as e:
            logger.error(f"加载代码库数据失败: {e}")

    def _save_codebases(self):
        """保存代码库数据"""
        try:
            import json

            data = {
                "codebases": [
                    self._codebase_to_dict(cb) for cb in self._codebases.values()
                ],
                "updated_at": datetime.now().isoformat(),
            }

            with open(self.codebases_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存代码库数据失败: {e}")

    def _codebase_to_dict(self, codebase: CodebaseInfo) -> Dict:
        """将代码库对象转换为字典"""
        return {
            "id": codebase.id,
            "name": codebase.name,
            "description": codebase.description,
            "root_path": codebase.root_path,
            "created_at": codebase.created_at.isoformat(),
            "updated_at": codebase.updated_at.isoformat(),
            "tags": codebase.tags,
            "language_primary": codebase.language_primary,
            "size_mb": codebase.size_mb,
            "metadata": codebase.metadata,
        }

    def _dict_to_codebase(self, data: Dict) -> CodebaseInfo:
        """将字典转换为代码库对象"""
        return CodebaseInfo(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            root_path=data["root_path"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tags=data.get("tags", []),
            language_primary=data.get("language_primary"),
            size_mb=data.get("size_mb", 0.0),
            metadata=data.get("metadata", {}),
        )

    def create_codebase(
        self,
        name: str,
        description: str,
        root_path: str,
        tags: Optional[List[str]] = None,
        language_primary: Optional[str] = None,
        metadata: Optional[Dict] = None,
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

        Returns:
            CodebaseInfo: 创建的代码库信息
        """
        try:
            # 检查路径是否存在
            if not os.path.exists(root_path):
                logger.error(f"代码库路径不存在: {root_path}")
                return None

            # 计算代码库大小
            size_mb = self._calculate_directory_size(root_path)

            # 创建代码库信息
            codebase = CodebaseInfo(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                root_path=root_path,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=tags or [],
                language_primary=language_primary,
                size_mb=size_mb,
                metadata=metadata or {},
            )

            # 保存到内存和文件
            self._codebases[codebase.id] = codebase
            self._save_codebases()

            logger.info(f"代码库创建成功: {codebase.name} (ID: {codebase.id})")
            return codebase

        except Exception as e:
            logger.error(f"创建代码库失败: {e}")
            return None

    def get_codebase(self, codebase_id: str) -> Optional[CodebaseInfo]:
        """
        获取代码库信息

        Args:
            codebase_id: 代码库ID

        Returns:
            CodebaseInfo: 代码库信息
        """
        return self._codebases.get(codebase_id)

    def list_codebases(self, tags: Optional[List[str]] = None) -> List[CodebaseInfo]:
        """
        列出所有代码库

        Args:
            tags: 筛选标签

        Returns:
            List[CodebaseInfo]: 代码库列表
        """
        codebases = list(self._codebases.values())

        if tags:
            codebases = [cb for cb in codebases if any(tag in cb.tags for tag in tags)]

        return sorted(codebases, key=lambda x: x.updated_at, reverse=True)

    def update_codebase(self, codebase_id: str, **updates) -> Optional[CodebaseInfo]:
        """
        更新代码库信息

        Args:
            codebase_id: 代码库ID
            **updates: 更新字段

        Returns:
            CodebaseInfo: 更新后的代码库信息
        """
        try:
            codebase = self._codebases.get(codebase_id)
            if not codebase:
                logger.error(f"代码库不存在: {codebase_id}")
                return None

            # 更新字段
            for field, value in updates.items():
                if hasattr(codebase, field):
                    setattr(codebase, field, value)

            codebase.updated_at = datetime.now()

            # 保存更新
            self._save_codebases()

            logger.info(f"代码库更新成功: {codebase.name}")
            return codebase

        except Exception as e:
            logger.error(f"更新代码库失败: {e}")
            return None

    def delete_codebase(self, codebase_id: str) -> bool:
        """
        删除代码库

        Args:
            codebase_id: 代码库ID

        Returns:
            bool: 删除是否成功
        """
        try:
            if codebase_id not in self._codebases:
                logger.error(f"代码库不存在: {codebase_id}")
                return False

            codebase_name = self._codebases[codebase_id].name

            # 从内存中删除
            del self._codebases[codebase_id]

            # 删除分析结果文件
            analysis_file = self.analysis_results_dir / f"{codebase_id}.json"
            if analysis_file.exists():
                analysis_file.unlink()

            # 保存更新
            self._save_codebases()

            logger.info(f"代码库删除成功: {codebase_name}")
            return True

        except Exception as e:
            logger.error(f"删除代码库失败: {e}")
            return False

    def save_analysis_result(self, codebase_id: str, result: AnalysisResult) -> bool:
        """
        保存分析结果

        Args:
            codebase_id: 代码库ID
            result: 分析结果

        Returns:
            bool: 保存是否成功
        """
        try:
            import json

            analysis_file = self.analysis_results_dir / f"{codebase_id}.json"

            # 手动构建可序列化的字典
            result_dict = {
                "codebase_id": result.codebase_id,
                "analysis_time": result.analysis_time.isoformat(),
                "tech_stacks": [
                    {
                        "name": ts.name,
                        "version": ts.version,
                        "type": ts.type.value,
                        "confidence": ts.confidence,
                        "description": ts.description,
                        "used_files": ts.used_files,
                    }
                    for ts in result.tech_stacks
                ],
                "components": [
                    {
                        "name": comp.name,
                        "type": comp.type.value,
                        "file_path": comp.file_path,
                        "start_line": comp.start_line,
                        "end_line": comp.end_line,
                        "complexity": comp.complexity.value,
                        "dependencies": comp.dependencies,
                        "description": comp.description,
                        "parameters": comp.parameters,
                        "return_type": comp.return_type,
                    }
                    for comp in result.components
                ],
                "similarities": [
                    {
                        "file1": sim.file1,
                        "file2": sim.file2,
                        "similarity_score": sim.similarity_score,
                        "similar_components": sim.similar_components,
                        "similarity_type": sim.similarity_type,
                        "details": sim.details,
                    }
                    for sim in result.similarities
                ],
                "metrics": {
                    "lines_of_code": result.metrics.lines_of_code,
                    "lines_of_comments": result.metrics.lines_of_comments,
                    "cyclomatic_complexity": result.metrics.cyclomatic_complexity,
                    "maintainability_index": result.metrics.maintainability_index,
                    "code_duplication_ratio": result.metrics.code_duplication_ratio,
                    "test_coverage": result.metrics.test_coverage,
                    "technical_debt_ratio": result.metrics.technical_debt_ratio,
                },
                "file_count": result.file_count,
                "total_lines": result.total_lines,
                "languages": result.languages,
                "estimated_effort_days": result.estimated_effort_days,
                "reusability_score": result.reusability_score,
                "suggestions": result.suggestions,
            }

            with open(analysis_file, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)

            logger.info(f"分析结果保存成功: {codebase_id}")
            return True

        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return False

    def load_analysis_result(self, codebase_id: str) -> Optional[AnalysisResult]:
        """
        加载分析结果

        Args:
            codebase_id: 代码库ID

        Returns:
            AnalysisResult: 分析结果
        """
        try:
            analysis_file = self.analysis_results_dir / f"{codebase_id}.json"

            if not analysis_file.exists():
                return None

            import json
            from datetime import datetime

            from .types import (
                AnalysisResult,
                CodeComplexity,
                CodeComponent,
                CodeMetrics,
                ComponentType,
                SimilarityResult,
                TechStack,
                TechStackType,
            )

            with open(analysis_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 反序列化TechStack列表
            tech_stacks = []
            for ts_data in data.get("tech_stacks", []):
                tech_stack = TechStack(
                    name=ts_data["name"],
                    version=ts_data["version"],
                    type=TechStackType(ts_data["type"]),
                    confidence=ts_data["confidence"],
                    description=ts_data["description"],
                    used_files=ts_data["used_files"],
                )
                tech_stacks.append(tech_stack)

            # 反序列化CodeComponent列表
            components = []
            for comp_data in data.get("components", []):
                component = CodeComponent(
                    name=comp_data["name"],
                    type=ComponentType(comp_data["type"]),
                    file_path=comp_data["file_path"],
                    start_line=comp_data["start_line"],
                    end_line=comp_data["end_line"],
                    complexity=CodeComplexity(comp_data["complexity"]),
                    dependencies=comp_data["dependencies"],
                    description=comp_data["description"],
                    parameters=comp_data["parameters"],
                    return_type=comp_data["return_type"],
                )
                components.append(component)

            # 反序列化SimilarityResult列表
            similarities = []
            for sim_data in data.get("similarities", []):
                similarity = SimilarityResult(
                    file1=sim_data["file1"],
                    file2=sim_data["file2"],
                    similarity_score=sim_data["similarity_score"],
                    similar_components=sim_data["similar_components"],
                    similarity_type=sim_data["similarity_type"],
                    details=sim_data["details"],
                )
                similarities.append(similarity)

            # 反序列化CodeMetrics
            metrics_data = data.get("metrics", {})
            metrics = CodeMetrics(
                lines_of_code=metrics_data["lines_of_code"],
                lines_of_comments=metrics_data["lines_of_comments"],
                cyclomatic_complexity=metrics_data["cyclomatic_complexity"],
                maintainability_index=metrics_data["maintainability_index"],
                code_duplication_ratio=metrics_data["code_duplication_ratio"],
                test_coverage=metrics_data["test_coverage"],
                technical_debt_ratio=metrics_data["technical_debt_ratio"],
            )

            # 创建AnalysisResult对象
            result = AnalysisResult(
                codebase_id=data["codebase_id"],
                analysis_time=datetime.fromisoformat(data["analysis_time"]),
                tech_stacks=tech_stacks,
                components=components,
                similarities=similarities,
                metrics=metrics,
                file_count=data["file_count"],
                total_lines=data["total_lines"],
                languages=data["languages"],
                estimated_effort_days=data["estimated_effort_days"],
                reusability_score=data["reusability_score"],
                suggestions=data["suggestions"],
            )

            return result

        except Exception as e:
            logger.error(f"加载分析结果失败: {e}")
            return None

    def _calculate_directory_size(self, directory: str) -> float:
        """
        计算目录大小（MB）

        Args:
            directory: 目录路径

        Returns:
            float: 目录大小（MB）
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.warning(f"计算目录大小失败: {e}")

        return total_size / (1024 * 1024)  # 转换为MB

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        total_codebases = len(self._codebases)
        total_size_mb = sum(cb.size_mb for cb in self._codebases.values())

        # 按语言统计
        language_stats = {}
        for cb in self._codebases.values():
            if cb.language_primary:
                language_stats[cb.language_primary] = (
                    language_stats.get(cb.language_primary, 0) + 1
                )

        # 按标签统计
        tag_stats = {}
        for cb in self._codebases.values():
            for tag in cb.tags:
                tag_stats[tag] = tag_stats.get(tag, 0) + 1

        return {
            "total_codebases": total_codebases,
            "total_size_mb": round(total_size_mb, 2),
            "language_distribution": language_stats,
            "tag_distribution": tag_stats,
            "average_size_mb": round(total_size_mb / max(total_codebases, 1), 2),
        }
