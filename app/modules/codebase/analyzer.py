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
from typing import Dict, List, Optional, Set, Tuple

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
            tree = ast.parse(content)

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
            logger.warning(f"解析Python文件失败 {file_path}: {e}")
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

        result = AnalysisResult(
            codebase_id=codebase_id,
            analysis_time=datetime.now(),
            tech_stacks=tech_stacks,
            components=components,
            metrics=metrics,
            file_count=file_count,
            total_lines=total_lines,
            languages=languages,
            estimated_effort_days=estimated_effort,
            reusability_score=reusability_score,
            suggestions=suggestions,
        )

        logger.info(f"代码库分析完成: {len(components)} 个组件, {file_count} 个文件")
        return result

    def _load_tech_stack_patterns(self) -> Dict:
        """加载技术栈识别模式"""
        return {
            "package.json": [
                (r'"react":', TechStack("React", type=TechStackType.FRONTEND)),
                (r'"vue":', TechStack("Vue.js", type=TechStackType.FRONTEND)),
                (r'"angular":', TechStack("Angular", type=TechStackType.FRONTEND)),
                (r'"express":', TechStack("Express.js", type=TechStackType.BACKEND)),
                (r'"next":', TechStack("Next.js", type=TechStackType.FRONTEND)),
                (
                    r'"typescript":',
                    TechStack("TypeScript", type=TechStackType.FRONTEND),
                ),
            ],
            "requirements.txt": [
                (r"django", TechStack("Django", type=TechStackType.BACKEND)),
                (r"flask", TechStack("Flask", type=TechStackType.BACKEND)),
                (r"fastapi", TechStack("FastAPI", type=TechStackType.BACKEND)),
                (r"pandas", TechStack("Pandas", type=TechStackType.AI_ML)),
                (r"numpy", TechStack("NumPy", type=TechStackType.AI_ML)),
                (r"tensorflow", TechStack("TensorFlow", type=TechStackType.AI_ML)),
                (r"pytorch", TechStack("PyTorch", type=TechStackType.AI_ML)),
            ],
            "pom.xml": [
                (r"spring-boot", TechStack("Spring Boot", type=TechStackType.BACKEND)),
                (
                    r"spring-framework",
                    TechStack("Spring Framework", type=TechStackType.BACKEND),
                ),
            ],
            "Gemfile": [
                (r"rails", TechStack("Ruby on Rails", type=TechStackType.BACKEND)),
            ],
            "go.mod": [
                (r"gin-gonic/gin", TechStack("Gin", type=TechStackType.BACKEND)),
                (r"gorilla/mux", TechStack("Gorilla Mux", type=TechStackType.BACKEND)),
            ],
        }

    def _identify_tech_stacks(
        self, root_path: str, languages: Dict[str, int]
    ) -> List[TechStack]:
        """识别技术栈"""
        tech_stacks = []

        # 基于语言的技术栈
        for language, line_count in languages.items():
            confidence = min(1.0, line_count / 1000)  # 简化的置信度计算
            tech_stacks.append(
                TechStack(
                    name=language.title(),
                    type=self._get_language_type(language),
                    confidence=confidence,
                    description=f"主要编程语言，代码行数: {line_count}",
                )
            )

        # 基于配置文件的技术栈
        for filename, patterns in self.tech_stack_patterns.items():
            config_path = os.path.join(root_path, filename)
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    for pattern, tech_stack in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            tech_stack.confidence = 0.9
                            tech_stack.used_files = [filename]
                            tech_stacks.append(tech_stack)

                except Exception as e:
                    logger.warning(f"读取配置文件失败 {config_path}: {e}")

        return tech_stacks

    def _get_language_type(self, language: str) -> TechStackType:
        """获取语言类型"""
        frontend_languages = {"javascript", "typescript", "html", "css"}
        backend_languages = {"python", "java", "go", "ruby", "php", "csharp"}

        if language.lower() in frontend_languages:
            return TechStackType.FRONTEND
        elif language.lower() in backend_languages:
            return TechStackType.BACKEND
        else:
            return TechStackType.OTHER

    def _count_files(self, root_path: str) -> int:
        """统计文件数量"""
        file_count = 0
        for root, dirs, files in os.walk(root_path):
            # 跳过非代码目录
            dirs[:] = [
                d
                for d in dirs
                if d not in {".git", ".svn", "node_modules", "__pycache__"}
            ]
            file_count += len(files)
        return file_count

    def _estimate_workload(
        self, components: List[CodeComponent], metrics: CodeMetrics
    ) -> float:
        """估算工作量（天）"""
        # 简化的工作量估算模型
        # 基于代码行数、复杂度等因素

        base_days = metrics.lines_of_code / 200  # 假设每天能写200行代码

        # 复杂度调整
        complexity_factor = 1.0
        for component in components:
            if component.complexity == CodeComplexity.HIGH:
                complexity_factor += 0.1
            elif component.complexity == CodeComplexity.VERY_HIGH:
                complexity_factor += 0.2

        estimated_days = base_days * complexity_factor
        return round(estimated_days, 1)

    def _calculate_reusability_score(
        self, components: List[CodeComponent], metrics: CodeMetrics
    ) -> float:
        """计算可复用性评分"""
        score = 50.0  # 基础分

        # 注释率影响
        if metrics.lines_of_code > 0:
            comment_ratio = metrics.lines_of_comments / metrics.lines_of_code
            score += comment_ratio * 30  # 注释率贡献最多30分

        # 模块化程度（函数和类的比例）
        total_components = len(components)
        if total_components > 0:
            modular_components = len(
                [
                    c
                    for c in components
                    if c.type in {ComponentType.FUNCTION, ComponentType.CLASS}
                ]
            )
            modular_ratio = modular_components / total_components
            score += modular_ratio * 20  # 模块化贡献最多20分

        return min(100.0, score)

    def _generate_suggestions(
        self,
        components: List[CodeComponent],
        metrics: CodeMetrics,
        tech_stacks: List[TechStack],
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 代码质量建议
        if metrics.lines_of_code > 0:
            comment_ratio = metrics.lines_of_comments / metrics.lines_of_code
            if comment_ratio < 0.1:
                suggestions.append("建议增加代码注释，提高代码可读性")

        # 复杂度建议
        complex_components = [
            c for c in components if c.complexity == CodeComplexity.VERY_HIGH
        ]
        if complex_components:
            suggestions.append(
                f"发现 {len(complex_components)} 个高复杂度组件，建议重构"
            )

        # 技术栈建议
        if not any(ts.type == TechStackType.TESTING for ts in tech_stacks):
            suggestions.append("建议添加测试框架，提高代码质量")

        # 文档建议
        if not any("README" in ts.name for ts in tech_stacks):
            suggestions.append("建议添加项目文档和README文件")

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
