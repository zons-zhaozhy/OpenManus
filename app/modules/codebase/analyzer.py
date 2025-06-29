"""
代码库分析器模块
提供代码结构分析、相似度检测、技术栈识别等功能
"""

import ast
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from .types import (
    AnalysisResult,
    CodeComplexity,
    CodeComponent,
    CodeMetrics,
    ComponentType,
    QualityIssue,
    SimilarityResult,
    TechStack,
    TechStackType,
    WorkloadEstimation,
)


class StructureAnalyzer:
    """代码结构分析器"""

    def __init__(self):
        """初始化结构分析器"""
        self.supported_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".kt": "kotlin",
            ".swift": "swift",
        }

    def analyze_structure(
        self, root_path: str
    ) -> Tuple[List[CodeComponent], CodeMetrics, Dict[str, int]]:
        """
        分析代码结构

        Args:
            root_path: 代码库根路径

        Returns:
            Tuple: (组件列表, 代码度量, 语言分布)
        """
        components = []
        total_lines = 0
        total_comment_lines = 0
        language_distribution = defaultdict(int)

        for file_path in self._get_code_files(root_path):
            try:
                file_components, file_metrics = self._analyze_file(file_path)
                components.extend(file_components)

                total_lines += file_metrics["lines"]
                total_comment_lines += file_metrics["comment_lines"]

                # 统计语言分布
                ext = Path(file_path).suffix.lower()
                if ext in self.supported_extensions:
                    language = self.supported_extensions[ext]
                    language_distribution[language] += file_metrics["lines"]

            except Exception as e:
                logger.warning(f"分析文件失败 {file_path}: {e}")

        # 计算整体度量
        metrics = CodeMetrics(
            lines_of_code=total_lines,
            lines_of_comments=total_comment_lines,
            cyclomatic_complexity=self._calculate_complexity(components),
            maintainability_index=self._calculate_maintainability(
                total_lines, total_comment_lines
            ),
        )

        return components, metrics, dict(language_distribution)

    def _get_code_files(self, root_path: str) -> List[str]:
        """获取所有代码文件"""
        code_files = []

        for root, dirs, files in os.walk(root_path):
            # 跳过常见的非代码目录
            dirs[:] = [
                d
                for d in dirs
                if d
                not in {
                    ".git",
                    ".svn",
                    "node_modules",
                    "__pycache__",
                    ".pytest_cache",
                    "dist",
                    "build",
                    "target",
                    "bin",
                    "obj",
                    ".idea",
                    ".vscode",
                }
            ]

            for file in files:
                file_path = os.path.join(root, file)
                ext = Path(file).suffix.lower()

                if ext in self.supported_extensions:
                    code_files.append(file_path)

        return code_files

    def _analyze_file(self, file_path: str) -> Tuple[List[CodeComponent], Dict]:
        """分析单个文件"""
        ext = Path(file_path).suffix.lower()

        if ext == ".py":
            return self._analyze_python_file(file_path)
        else:
            return self._analyze_generic_file(file_path)

    def _analyze_python_file(self, file_path: str) -> Tuple[List[CodeComponent], Dict]:
        """分析Python文件"""
        components = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 计算行数和注释行数
            lines = content.split("\n")
            total_lines = len(lines)
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))

            # 解析AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                logger.warning(f"解析Python文件失败 {file_path}: {e}")
                # 回退到通用分析
                return self._analyze_generic_file(file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    components.append(
                        CodeComponent(
                            name=node.name,
                            type=ComponentType.FUNCTION,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            complexity=self._estimate_function_complexity(node),
                            parameters=[arg.arg for arg in node.args.args],
                            return_type=self._get_return_annotation(node),
                        )
                    )
                elif isinstance(node, ast.ClassDef):
                    components.append(
                        CodeComponent(
                            name=node.name,
                            type=ComponentType.CLASS,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            complexity=self._estimate_class_complexity(node),
                        )
                    )

        except Exception as e:
            logger.warning(f"分析Python文件失败 {file_path}: {e}")
            # 回退到通用分析
            return self._analyze_generic_file(file_path)

        return components, {"lines": total_lines, "comment_lines": comment_lines}

    def _analyze_generic_file(self, file_path: str) -> Tuple[List[CodeComponent], Dict]:
        """通用文件分析"""
        components = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            total_lines = len(lines)

            # 简单的注释行检测
            comment_patterns = [r"^\s*//", r"^\s*#", r"^\s*/\*", r"^\s*\*"]
            comment_lines = 0

            for line in lines:
                for pattern in comment_patterns:
                    if re.match(pattern, line):
                        comment_lines += 1
                        break

            # 简单的函数检测（基于模式匹配）
            function_patterns = [
                (r"def\s+(\w+)\s*\(", ComponentType.FUNCTION),  # Python
                (r"function\s+(\w+)\s*\(", ComponentType.FUNCTION),  # JavaScript
                (r"(\w+)\s*\([^)]*\)\s*{", ComponentType.FUNCTION),  # C/Java style
                (r"class\s+(\w+)", ComponentType.CLASS),  # Class definitions
            ]

            for i, line in enumerate(lines, 1):
                for pattern, comp_type in function_patterns:
                    match = re.search(pattern, line)
                    if match:
                        components.append(
                            CodeComponent(
                                name=match.group(1),
                                type=comp_type,
                                file_path=file_path,
                                start_line=i,
                                end_line=i,
                                complexity=CodeComplexity.LOW,
                            )
                        )

        except Exception as e:
            logger.warning(f"通用文件分析失败 {file_path}: {e}")
            return [], {"lines": 0, "comment_lines": 0}

        return components, {"lines": total_lines, "comment_lines": comment_lines}

    def _estimate_function_complexity(self, node: ast.FunctionDef) -> CodeComplexity:
        """估算函数复杂度"""
        complexity_score = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity_score += 1
            elif isinstance(child, ast.BoolOp):
                complexity_score += len(child.values) - 1

        if complexity_score <= 5:
            return CodeComplexity.LOW
        elif complexity_score <= 10:
            return CodeComplexity.MEDIUM
        elif complexity_score <= 20:
            return CodeComplexity.HIGH
        else:
            return CodeComplexity.VERY_HIGH

    def _estimate_class_complexity(self, node: ast.ClassDef) -> CodeComplexity:
        """估算类复杂度"""
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])

        if method_count <= 5:
            return CodeComplexity.LOW
        elif method_count <= 10:
            return CodeComplexity.MEDIUM
        elif method_count <= 20:
            return CodeComplexity.HIGH
        else:
            return CodeComplexity.VERY_HIGH

    def _get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """获取函数返回类型注解"""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            elif isinstance(node.returns, ast.Constant):
                return str(node.returns.value)
        return None

    def _calculate_complexity(self, components: List[CodeComponent]) -> int:
        """计算整体复杂度"""
        complexity_map = {
            CodeComplexity.LOW: 1,
            CodeComplexity.MEDIUM: 3,
            CodeComplexity.HIGH: 7,
            CodeComplexity.VERY_HIGH: 15,
        }

        return sum(complexity_map.get(comp.complexity, 1) for comp in components)

    def _calculate_maintainability(self, total_lines: int, comment_lines: int) -> float:
        """计算可维护性指数"""
        if total_lines == 0:
            return 0.0

        comment_ratio = comment_lines / total_lines
        # 简化的可维护性计算，实际应该更复杂
        return min(100.0, 80.0 + comment_ratio * 20.0)


class CodeAnalyzer:
    """代码分析器"""

    def __init__(self):
        """初始化代码分析器"""
        self.structure_analyzer = StructureAnalyzer()
        self.tech_stack_patterns = self._load_tech_stack_patterns()
        self.analysis_cache = {}

    def analyze_codebase(self, codebase_id: str, root_path: str) -> AnalysisResult:
        """
        分析代码库

        Args:
            codebase_id: 代码库ID
            root_path: 代码库根路径

        Returns:
            AnalysisResult: 分析结果
        """
        logger.info(f"开始分析代码库: {root_path}")

        try:
            # 检查缓存
            cache_key = f"{codebase_id}:{root_path}"
            if cache_key in self.analysis_cache:
                cached_result = self.analysis_cache[cache_key]
                if (
                    datetime.now() - cached_result["timestamp"]
                ).total_seconds() < 300:  # 5分钟缓存
                    logger.info("使用缓存的分析结果")
                    return cached_result["result"]

            # 结构分析
            components, metrics, languages = self.structure_analyzer.analyze_structure(
                root_path
            )

            # 技术栈识别
            tech_stacks = self._identify_tech_stacks(root_path, languages)

            # 文件统计
            file_count = self._count_files(root_path)
            total_lines = metrics.lines_of_code

            # 工作量估算
            estimated_effort = self._estimate_workload(components, metrics)

            # 可复用性评分
            reusability_score = self._calculate_reusability_score(components, metrics)

            # 生成建议
            suggestions = self._generate_suggestions(components, metrics, tech_stacks)

            # 质量问题分析
            quality_issues = self._analyze_quality_issues(components, metrics)

            result = AnalysisResult(
                components=components,
                metrics=metrics,
                languages=languages,
                tech_stacks=tech_stacks,
                file_count=file_count,
                total_lines=total_lines,
                estimated_effort=estimated_effort,
                reusability_score=reusability_score,
                suggestions=suggestions,
                quality_issues=quality_issues,
            )

            # 更新缓存
            self.analysis_cache[cache_key] = {
                "result": result,
                "timestamp": datetime.now(),
            }

            logger.info("代码库分析完成")
            return result

        except Exception as e:
            logger.error(f"代码库分析失败: {str(e)}")
            raise

    def _analyze_quality_issues(
        self, components: List[CodeComponent], metrics: CodeMetrics
    ) -> List[QualityIssue]:
        """分析质量问题"""
        issues = []

        # 检查复杂度过高的组件
        for component in components:
            if component.complexity == CodeComplexity.HIGH:
                issues.append(
                    QualityIssue(
                        title=f"复杂度过高: {component.name}",
                        description=f"组件 {component.name} 的复杂度过高，建议重构拆分",
                        severity="HIGH",
                        file_path=component.file_path,
                        line_number=component.start_line,
                    )
                )

        # 检查注释率
        if metrics.lines_of_code > 0:
            comment_ratio = metrics.lines_of_comments / metrics.lines_of_code
            if comment_ratio < 0.1:  # 注释率低于10%
                issues.append(
                    QualityIssue(
                        title="注释率过低",
                        description="代码注释率低于10%，建议增加必要的注释",
                        severity="MEDIUM",
                    )
                )

        # 检查文件大小
        for component in components:
            if component.end_line - component.start_line > 500:  # 文件超过500行
                issues.append(
                    QualityIssue(
                        title=f"文件过大: {component.name}",
                        description=f"文件 {component.name} 超过500行，建议拆分",
                        severity="MEDIUM",
                        file_path=component.file_path,
                        line_number=component.start_line,
                    )
                )

        return issues

    def _load_tech_stack_patterns(self) -> Dict[str, List[str]]:
        """加载技术栈模式"""
        return {
            "frontend": [
                "react",
                "vue",
                "angular",
                "webpack",
                "babel",
                "typescript",
                "sass",
                "less",
            ],
            "backend": [
                "django",
                "flask",
                "fastapi",
                "express",
                "spring",
                "laravel",
                "rails",
            ],
            "database": [
                "mysql",
                "postgresql",
                "mongodb",
                "redis",
                "elasticsearch",
                "sqlite",
            ],
            "testing": ["pytest", "jest", "mocha", "junit", "selenium", "cypress"],
            "deployment": [
                "docker",
                "kubernetes",
                "jenkins",
                "travis",
                "gitlab-ci",
                "github-actions",
            ],
        }

    def _identify_tech_stacks(
        self, root_path: str, languages: Dict[str, int]
    ) -> List[TechStack]:
        """识别技术栈"""
        tech_stacks = []

        # 根据文件内容识别技术栈
        for root, _, files in os.walk(root_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().lower()

                    # 检查每个技术栈类型
                    for stack_type, patterns in self.tech_stack_patterns.items():
                        for pattern in patterns:
                            if pattern in content:
                                tech_stacks.append(
                                    TechStack(
                                        name=pattern,
                                        type=TechStackType(stack_type.upper()),
                                        confidence=0.8,
                                    )
                                )
                except Exception:
                    continue

        # 根据语言分布添加主要语言
        for language, lines in languages.items():
            if lines > 100:  # 超过100行的语言被认为是主要语言
                tech_stacks.append(
                    TechStack(
                        name=language,
                        type=TechStackType.LANGUAGE,
                        confidence=1.0,
                    )
                )

        return list(set(tech_stacks))  # 去重

    def _count_files(self, root_path: str) -> int:
        """统计文件数量"""
        count = 0
        for root, _, files in os.walk(root_path):
            # 跳过常见的非代码目录
            if any(
                part in root
                for part in [
                    ".git",
                    "node_modules",
                    "__pycache__",
                    "venv",
                    "dist",
                    "build",
                ]
            ):
                continue
            count += len(files)
        return count

    def _estimate_workload(
        self, components: List[CodeComponent], metrics: CodeMetrics
    ) -> float:
        """估算工作量（人天）"""
        base_effort = metrics.lines_of_code / 100  # 每100行代码1人天

        # 根据复杂度调整
        complexity_factor = 1.0
        high_complexity_count = sum(
            1 for c in components if c.complexity == CodeComplexity.HIGH
        )
        if high_complexity_count > 0:
            complexity_factor += 0.2 * high_complexity_count

        # 根据技术栈数量调整
        tech_stack_factor = 1.0 + len(set(c.type for c in components)) * 0.1

        # 根据维护性指数调整
        maintainability_factor = (
            2.0 - metrics.maintainability_index / 100
            if metrics.maintainability_index > 0
            else 2.0
        )

        return (
            base_effort * complexity_factor * tech_stack_factor * maintainability_factor
        )

    def _calculate_reusability_score(
        self, components: List[CodeComponent], metrics: CodeMetrics
    ) -> float:
        """计算可复用性评分（0-100）"""
        # 基础分数
        base_score = 70

        # 根据组件数量和复杂度调整
        component_score = 0
        for component in components:
            if component.complexity == CodeComplexity.LOW:
                component_score += 5
            elif component.complexity == CodeComplexity.MEDIUM:
                component_score += 3
            else:
                component_score -= 2

        # 根据注释率调整
        comment_ratio = (
            metrics.lines_of_comments / metrics.lines_of_code
            if metrics.lines_of_code > 0
            else 0
        )
        comment_score = min(comment_ratio * 100, 20)  # 最高20分

        # 根据维护性指数调整
        maintainability_score = metrics.maintainability_index / 5  # 最高20分

        final_score = (
            base_score + component_score + comment_score + maintainability_score
        )
        return max(0, min(100, final_score))  # 确保分数在0-100之间

    def _generate_suggestions(
        self,
        components: List[CodeComponent],
        metrics: CodeMetrics,
        tech_stacks: List[TechStack],
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 复杂度建议
        high_complexity_components = [
            c for c in components if c.complexity == CodeComplexity.HIGH
        ]
        if high_complexity_components:
            suggestions.append(
                f"发现 {len(high_complexity_components)} 个高复杂度组件，建议进行重构拆分"
            )

        # 注释建议
        if metrics.lines_of_code > 0:
            comment_ratio = metrics.lines_of_comments / metrics.lines_of_code
            if comment_ratio < 0.1:
                suggestions.append("代码注释率较低，建议增加必要的注释")

        # 维护性建议
        if metrics.maintainability_index < 50:
            suggestions.append("代码维护性较差，建议改进代码结构和文档")

        # 技术栈建议
        tech_stack_types = set(t.type for t in tech_stacks)
        if len(tech_stack_types) > 5:
            suggestions.append("技术栈过于复杂，建议适当简化")

        return suggestions


class SimilarityAnalyzer:
    """代码相似度分析器"""

    def __init__(self):
        """初始化相似度分析器"""
        pass

    def analyze_similarity(self, codebase_path: str) -> List[SimilarityResult]:
        """
        分析代码相似度

        Args:
            codebase_path: 代码库路径

        Returns:
            List[SimilarityResult]: 相似度结果列表
        """
        similarities = []
        code_files = self._get_code_files(codebase_path)

        # 比较所有文件对
        for i, file1 in enumerate(code_files):
            for j, file2 in enumerate(code_files[i + 1 :], i + 1):
                similarity = self._calculate_file_similarity(file1, file2)
                if similarity > 0.7:  # 只保留高相似度的结果
                    similarities.append(
                        SimilarityResult(
                            file1=file1,
                            file2=file2,
                            similarity_score=similarity,
                            similarity_type="structural",
                        )
                    )

        return similarities

    def _get_code_files(self, root_path: str) -> List[str]:
        """获取代码文件列表"""
        code_files = []
        extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"}

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [
                d for d in dirs if d not in {".git", "node_modules", "__pycache__"}
            ]

            for file in files:
                if Path(file).suffix.lower() in extensions:
                    code_files.append(os.path.join(root, file))

        return code_files

    def _calculate_file_similarity(self, file1: str, file2: str) -> float:
        """计算两个文件的相似度"""
        try:
            with open(file1, "r", encoding="utf-8") as f:
                content1 = f.read()
            with open(file2, "r", encoding="utf-8") as f:
                content2 = f.read()

            # 简化的相似度计算（基于行的比较）
            lines1 = set(line.strip() for line in content1.split("\n") if line.strip())
            lines2 = set(line.strip() for line in content2.split("\n") if line.strip())

            if not lines1 and not lines2:
                return 1.0
            if not lines1 or not lines2:
                return 0.0

            intersection = len(lines1 & lines2)
            union = len(lines1 | lines2)

            return intersection / union if union > 0 else 0.0

        except Exception as e:
            logger.warning(f"计算文件相似度失败 {file1} vs {file2}: {e}")
            return 0.0


class CodebaseAnalyzer:
    """代码库分析器"""

    def __init__(self):
        """初始化代码库分析器"""
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../..")
        )
        logger.debug(f"代码库分析器初始化，项目根目录: {self.project_root}")

    async def analyze_for_requirement(
        self, requirement_text: str
    ) -> List[Dict[str, Any]]:
        """根据需求文本分析相关代码组件

        Args:
            requirement_text: 需求文本

        Returns:
            List[Dict[str, Any]]: 相关代码组件列表
        """
        logger.debug(f"分析需求相关代码: {requirement_text[:30]}...")

        # 这里简化实现，返回一些基本组件
        # 在实际应用中，可以使用更复杂的代码分析逻辑
        components = [
            {
                "name": "RequirementsFlow",
                "type": "class",
                "path": "app/assistants/requirements/flow/requirements_flow.py",
                "description": "需求分析工作流核心类，负责协调各个智能体完成需求分析",
            },
            {
                "name": "RequirementClarifierAgent",
                "type": "class",
                "path": "app/assistants/requirements/agents/requirement_clarifier/agent.py",
                "description": "需求澄清智能体，负责提出澄清问题和整理需求",
            },
            {
                "name": "BusinessAnalystAgent",
                "type": "class",
                "path": "app/assistants/requirements/agents/business_analyst/agent.py",
                "description": "业务分析智能体，负责分析需求的业务价值和可行性",
            },
        ]

        logger.debug(f"找到 {len(components)} 个相关组件")
        return components

    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析单个文件

        Args:
            file_path: 文件路径

        Returns:
            Dict[str, Any]: 文件分析结果
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return {"error": "文件不存在"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单分析，实际应用中可以使用更复杂的代码分析
            lines = content.split("\n")
            classes = []
            functions = []
            imports = []

            for line in lines:
                line = line.strip()
                if line.startswith("class "):
                    class_name = line.split("class ")[1].split("(")[0].strip()
                    classes.append(class_name)
                elif line.startswith("def "):
                    func_name = line.split("def ")[1].split("(")[0].strip()
                    functions.append(func_name)
                elif line.startswith("import ") or line.startswith("from "):
                    imports.append(line)

            return {
                "path": file_path,
                "lines_count": len(lines),
                "classes": classes,
                "functions": functions,
                "imports": imports,
            }
        except Exception as e:
            logger.error(f"分析文件失败: {file_path}, 错误: {str(e)}")
            return {"error": str(e)}

    async def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        """分析目录

        Args:
            directory_path: 目录路径

        Returns:
            Dict[str, Any]: 目录分析结果
        """
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            logger.warning(f"目录不存在: {directory_path}")
            return {"error": "目录不存在"}

        try:
            results = []
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        file_result = await self.analyze_file(file_path)
                        results.append(file_result)

            return {
                "directory": directory_path,
                "files_count": len(results),
                "files": results,
            }
        except Exception as e:
            logger.error(f"分析目录失败: {directory_path}, 错误: {str(e)}")
            return {"error": str(e)}
