"""
代码库分析器

为需求分析提供代码理解和复用建议：
1. 分析现有代码库结构
2. 识别可复用组件和模式
3. 评估技术债务和改进建议
4. 提供实现复杂度估算
"""

import ast
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.logger import logger


@dataclass
class CodeComponent:
    """代码组件"""

    name: str
    type: str  # class, function, module, package
    file_path: str
    line_start: int
    line_end: int
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    complexity_score: int = 1  # 1-简单, 2-中等, 3-复杂
    reusability_score: float = 0.0  # 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodePattern:
    """代码模式"""

    name: str
    pattern_type: str  # design_pattern, architectural_pattern, coding_pattern
    description: str
    files: List[str] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    related_requirements: List[str] = field(default_factory=list)


@dataclass
class TechnicalDebt:
    """技术债务"""

    file_path: str
    issue_type: str  # code_smell, complexity, duplication, security
    description: str
    severity: str  # low, medium, high, critical
    effort_to_fix: str  # small, medium, large
    impact_on_requirements: str = ""


class CodeAnalyzer:
    """代码库分析器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.components: List[CodeComponent] = []
        self.patterns: List[CodePattern] = []
        self.technical_debts: List[TechnicalDebt] = []
        self.analysis_cache: Dict[str, Any] = {}

    def analyze_codebase(self, target_dirs: List[str] = None) -> Dict[str, Any]:
        """分析代码库"""
        logger.info("开始代码库分析")

        if target_dirs is None:
            target_dirs = ["app/", "src/", "lib/"]

        analysis_result = {
            "project_overview": self._get_project_overview(),
            "components": [],
            "patterns": [],
            "technical_debts": [],
            "reusability_recommendations": [],
            "complexity_analysis": {},
        }

        for target_dir in target_dirs:
            dir_path = os.path.join(self.project_root, target_dir)
            if os.path.exists(dir_path):
                self._analyze_directory(dir_path)

        # 识别设计模式
        self._identify_patterns()

        # 评估技术债务
        self._assess_technical_debt()

        # 生成复用建议
        reusability_recommendations = self._generate_reusability_recommendations()

        analysis_result.update(
            {
                "components": [self._component_to_dict(c) for c in self.components],
                "patterns": [self._pattern_to_dict(p) for p in self.patterns],
                "technical_debts": [
                    self._debt_to_dict(d) for d in self.technical_debts
                ],
                "reusability_recommendations": reusability_recommendations,
                "complexity_analysis": self._analyze_complexity(),
            }
        )

        logger.info(f"代码库分析完成，发现 {len(self.components)} 个组件")
        return analysis_result

    def _get_project_overview(self) -> Dict[str, Any]:
        """获取项目概览"""
        overview = {
            "project_root": self.project_root,
            "total_files": 0,
            "code_files": 0,
            "languages": {},
            "file_structure": {},
        }

        # 只分析项目目录，不遍历整个系统
        project_dirs_to_scan = ["app", "src", "lib", "tests"]

        for project_dir in project_dirs_to_scan:
            dir_path = os.path.join(self.project_root, project_dir)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    # 跳过常见的隐藏目录和缓存目录
                    dirs[:] = [
                        d
                        for d in dirs
                        if not d.startswith(".")
                        and d not in ["__pycache__", "node_modules", ".git"]
                    ]

                    for file in files:
                        if not file.startswith("."):
                            overview["total_files"] += 1

                            # 分析文件类型
                            ext = Path(file).suffix.lower()
                            if ext in [
                                ".py",
                                ".js",
                                ".ts",
                                ".java",
                                ".cpp",
                                ".c",
                                ".html",
                                ".css",
                            ]:
                                overview["code_files"] += 1
                                overview["languages"][ext] = (
                                    overview["languages"].get(ext, 0) + 1
                                )

        return overview

    def _analyze_directory(self, dir_path: str):
        """分析目录"""
        for root, dirs, files in os.walk(dir_path):
            # 跳过隐藏目录和缓存目录
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in ["__pycache__", "node_modules"]
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self._analyze_python_file(file_path)

    def _analyze_python_file(self, file_path: str):
        """分析Python文件"""
        try:
            # 跳过系统文件和非项目文件
            if not self._is_project_file(file_path):
                return

            # 尝试多种编码
            content = self._read_file_safely(file_path)
            if content is None:
                return

            tree = ast.parse(content)

            # 分析类
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    component = self._create_component_from_class(
                        node, file_path, content
                    )
                    self.components.append(component)

                elif isinstance(node, ast.FunctionDef):
                    # 只分析顶级函数（非类方法）
                    if isinstance(
                        node.parent if hasattr(node, "parent") else None, ast.Module
                    ):
                        component = self._create_component_from_function(
                            node, file_path, content
                        )
                        self.components.append(component)

        except Exception as e:
            logger.warning(f"分析文件 {file_path} 时出错: {e}")

    def _is_project_file(self, file_path: str) -> bool:
        """检查是否为项目文件"""
        # 排除系统路径
        system_paths = ["/usr/", "/Library/", "/System/", "/opt/", "/etc/"]
        return not any(file_path.startswith(path) for path in system_paths)

    def _read_file_safely(self, file_path: str) -> Optional[str]:
        """安全读取文件，处理编码问题"""
        encodings = ["utf-8", "gbk", "latin1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                break

        logger.warning(f"无法读取文件 {file_path}：编码问题")
        return None

    def _create_component_from_class(
        self, node: ast.ClassDef, file_path: str, content: str
    ) -> CodeComponent:
        """从类节点创建组件"""
        # 计算复杂度
        complexity = self._calculate_complexity(node)

        # 分析依赖
        dependencies = self._extract_dependencies(node)

        # 评估可复用性
        reusability = self._evaluate_reusability(node, file_path)

        return CodeComponent(
            name=node.name,
            type="class",
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            description=ast.get_docstring(node) or f"类 {node.name}",
            dependencies=dependencies,
            complexity_score=complexity,
            reusability_score=reusability,
            metadata={
                "methods": [
                    n.name for n in node.body if isinstance(n, ast.FunctionDef)
                ],
                "base_classes": [n.id for n in node.bases if isinstance(n, ast.Name)],
                "is_abstract": any(
                    isinstance(d, ast.Name) and d.id == "ABC" for d in node.bases
                ),
            },
        )

    def _create_component_from_function(
        self, node: ast.FunctionDef, file_path: str, content: str
    ) -> CodeComponent:
        """从函数节点创建组件"""
        complexity = self._calculate_complexity(node)
        dependencies = self._extract_dependencies(node)
        reusability = self._evaluate_reusability(node, file_path)

        return CodeComponent(
            name=node.name,
            type="function",
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            description=ast.get_docstring(node) or f"函数 {node.name}",
            dependencies=dependencies,
            complexity_score=complexity,
            reusability_score=reusability,
            metadata={
                "parameters": [arg.arg for arg in node.args.args],
                "returns": node.returns is not None,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            },
        )

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算代码复杂度（基于圈复杂度）"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            # 分支语句增加复杂度
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        # 根据复杂度值分级
        if complexity <= 5:
            return 1  # 简单
        elif complexity <= 10:
            return 2  # 中等
        else:
            return 3  # 复杂

    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        """提取依赖关系"""
        dependencies = []

        for child in ast.walk(node):
            if isinstance(child, ast.Import):
                for name in child.names:
                    dependencies.append(name.name)
            elif isinstance(child, ast.ImportFrom):
                if child.module:
                    dependencies.append(child.module)

        return list(set(dependencies))  # 去重

    def _evaluate_reusability(self, node: ast.AST, file_path: str) -> float:
        """评估可复用性"""
        score = 0.5  # 基础分数

        # 有文档字符串加分
        if ast.get_docstring(node):
            score += 0.2

        # 参数合理加分（对于函数）
        if isinstance(node, ast.FunctionDef):
            if len(node.args.args) <= 5:  # 参数不超过5个
                score += 0.1

        # 复杂度合理加分
        complexity = self._calculate_complexity(node)
        if complexity <= 2:
            score += 0.1

        # 在工具或基础模块中加分
        if any(
            keyword in file_path.lower()
            for keyword in ["util", "tool", "base", "common"]
        ):
            score += 0.1

        return min(1.0, score)

    def _identify_patterns(self):
        """识别设计模式"""
        # 识别单例模式
        self._identify_singleton_pattern()

        # 识别工厂模式
        self._identify_factory_pattern()

        # 识别观察者模式
        self._identify_observer_pattern()

        # 识别策略模式
        self._identify_strategy_pattern()

    def _identify_singleton_pattern(self):
        """识别单例模式"""
        for component in self.components:
            if component.type == "class":
                # 检查是否有__new__方法的单例实现
                methods = component.metadata.get("methods", [])
                if "__new__" in methods:
                    pattern = CodePattern(
                        name="单例模式",
                        pattern_type="design_pattern",
                        description=f"类 {component.name} 实现了单例模式",
                        files=[component.file_path],
                        benefits=["确保全局只有一个实例", "提供全局访问点"],
                        related_requirements=["全局配置管理", "资源管理", "状态管理"],
                    )
                    self.patterns.append(pattern)

    def _identify_factory_pattern(self):
        """识别工厂模式"""
        for component in self.components:
            if component.type == "class" and "factory" in component.name.lower():
                pattern = CodePattern(
                    name="工厂模式",
                    pattern_type="design_pattern",
                    description=f"类 {component.name} 实现了工厂模式",
                    files=[component.file_path],
                    benefits=["封装对象创建逻辑", "提高代码灵活性"],
                    related_requirements=["对象创建", "产品族管理", "插件系统"],
                )
                self.patterns.append(pattern)

    def _identify_observer_pattern(self):
        """识别观察者模式"""
        observer_keywords = ["observer", "listener", "event", "notify"]
        for component in self.components:
            if any(keyword in component.name.lower() for keyword in observer_keywords):
                pattern = CodePattern(
                    name="观察者模式",
                    pattern_type="design_pattern",
                    description=f"组件 {component.name} 参与观察者模式",
                    files=[component.file_path],
                    benefits=["松耦合", "动态订阅", "事件驱动"],
                    related_requirements=["事件通知", "状态变化响应", "解耦设计"],
                )
                self.patterns.append(pattern)

    def _identify_strategy_pattern(self):
        """识别策略模式"""
        strategy_keywords = ["strategy", "algorithm", "policy"]
        for component in self.components:
            if any(keyword in component.name.lower() for keyword in strategy_keywords):
                pattern = CodePattern(
                    name="策略模式",
                    pattern_type="design_pattern",
                    description=f"组件 {component.name} 实现了策略模式",
                    files=[component.file_path],
                    benefits=["算法可替换", "扩展性好", "符合开闭原则"],
                    related_requirements=["算法选择", "业务规则变化", "插件化"],
                )
                self.patterns.append(pattern)

    def _assess_technical_debt(self):
        """评估技术债务"""
        for component in self.components:
            # 检查复杂度过高
            if component.complexity_score >= 3:
                debt = TechnicalDebt(
                    file_path=component.file_path,
                    issue_type="complexity",
                    description=f"{component.type} {component.name} 复杂度过高",
                    severity="medium",
                    effort_to_fix="medium",
                    impact_on_requirements="可能影响维护性和扩展性",
                )
                self.technical_debts.append(debt)

            # 检查可复用性低
            if component.reusability_score < 0.3:
                debt = TechnicalDebt(
                    file_path=component.file_path,
                    issue_type="code_smell",
                    description=f"{component.type} {component.name} 可复用性较低",
                    severity="low",
                    effort_to_fix="small",
                    impact_on_requirements="可能需要重构以提高复用性",
                )
                self.technical_debts.append(debt)

    def _generate_reusability_recommendations(self) -> List[Dict[str, Any]]:
        """生成复用建议"""
        recommendations = []

        # 高复用性组件推荐
        high_reusability_components = [
            c for c in self.components if c.reusability_score >= 0.7
        ]
        if high_reusability_components:
            recommendations.append(
                {
                    "type": "reusable_components",
                    "title": "可复用组件推荐",
                    "description": "以下组件具有较高的复用价值，建议在新需求中优先考虑",
                    "components": [c.name for c in high_reusability_components],
                    "benefit": "减少开发工作量，提高代码一致性",
                }
            )

        # 模式复用推荐
        if self.patterns:
            recommendations.append(
                {
                    "type": "design_patterns",
                    "title": "设计模式复用",
                    "description": "项目中已使用的设计模式，可在类似需求中复用",
                    "patterns": [p.name for p in self.patterns],
                    "benefit": "保持架构一致性，降低学习成本",
                }
            )

        return recommendations

    def _analyze_complexity(self) -> Dict[str, Any]:
        """分析复杂度分布"""
        complexity_distribution = {"简单": 0, "中等": 0, "复杂": 0}
        complexity_mapping = {1: "简单", 2: "中等", 3: "复杂"}

        for component in self.components:
            complexity_level = complexity_mapping[component.complexity_score]
            complexity_distribution[complexity_level] += 1

        total_components = len(self.components)
        return {
            "distribution": complexity_distribution,
            "total_components": total_components,
            "average_complexity": sum(c.complexity_score for c in self.components)
            / max(total_components, 1),
            "high_complexity_ratio": complexity_distribution["复杂"]
            / max(total_components, 1),
        }

    def find_similar_implementations(
        self, requirement_text: str
    ) -> List[CodeComponent]:
        """根据需求文本查找相似的实现"""
        requirement_lower = requirement_text.lower()
        similar_components = []

        for component in self.components:
            # 检查名称相似度
            if (
                self._calculate_text_similarity(
                    requirement_lower, component.name.lower()
                )
                > 0.3
            ):
                similar_components.append(component)

            # 检查描述相似度
            elif (
                self._calculate_text_similarity(
                    requirement_lower, component.description.lower()
                )
                > 0.2
            ):
                similar_components.append(component)

        # 按复用性得分排序
        similar_components.sort(key=lambda x: x.reusability_score, reverse=True)
        return similar_components[:5]  # 返回前5个最相似的

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单实现）"""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def estimate_implementation_effort(self, requirement_text: str) -> Dict[str, Any]:
        """估算实现工作量"""
        # 查找相似实现
        similar_components = self.find_similar_implementations(requirement_text)

        # 基于相似组件评估
        if similar_components:
            avg_complexity = sum(c.complexity_score for c in similar_components) / len(
                similar_components
            )
            max_reusability = max(c.reusability_score for c in similar_components)

            # 复杂度影响工作量
            complexity_factor = {1: 0.5, 2: 1.0, 3: 2.0}[
                min(3, max(1, round(avg_complexity)))
            ]

            # 可复用性降低工作量
            reusability_factor = 1.0 - (max_reusability * 0.5)

            effort_score = complexity_factor * reusability_factor

            if effort_score <= 0.7:
                effort_level = "低"
                estimated_days = "1-3天"
            elif effort_score <= 1.3:
                effort_level = "中等"
                estimated_days = "3-7天"
            else:
                effort_level = "高"
                estimated_days = "7-14天"
        else:
            effort_level = "中等"
            estimated_days = "5-10天"
            similar_components = []

        return {
            "effort_level": effort_level,
            "estimated_days": estimated_days,
            "confidence": "中等" if similar_components else "低",
            "reusable_components": [c.name for c in similar_components],
            "recommendations": [
                "基于现有组件进行扩展" if similar_components else "需要新开发",
                "参考项目中的设计模式",
                "注意技术债务的影响",
            ],
        }

    def _component_to_dict(self, component: CodeComponent) -> Dict[str, Any]:
        """将组件转换为字典"""
        return {
            "name": component.name,
            "type": component.type,
            "file_path": component.file_path,
            "line_range": f"{component.line_start}-{component.line_end}",
            "description": component.description,
            "complexity_score": component.complexity_score,
            "reusability_score": component.reusability_score,
            "dependencies": component.dependencies,
            "metadata": component.metadata,
        }

    def _pattern_to_dict(self, pattern: CodePattern) -> Dict[str, Any]:
        """将模式转换为字典"""
        return {
            "name": pattern.name,
            "type": pattern.pattern_type,
            "description": pattern.description,
            "files": pattern.files,
            "benefits": pattern.benefits,
            "related_requirements": pattern.related_requirements,
        }

    def _debt_to_dict(self, debt: TechnicalDebt) -> Dict[str, Any]:
        """将技术债务转换为字典"""
        return {
            "file_path": debt.file_path,
            "issue_type": debt.issue_type,
            "description": debt.description,
            "severity": debt.severity,
            "effort_to_fix": debt.effort_to_fix,
            "impact_on_requirements": debt.impact_on_requirements,
        }
