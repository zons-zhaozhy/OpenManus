"""
代码分析器
"""

import ast
import os # 导入os模块
from typing import Any, Dict, List, Optional, Tuple

from app.logger import logger

from ..models.base import CodeComponent


class CodeAnalyzer:
    """代码分析器"""

    def analyze_class(
        self, node: ast.ClassDef, file_path: str, content: str
    ) -> CodeComponent:
        """分析类定义"""
        # 获取类的行范围
        line_start = node.lineno
        line_end = self._get_node_end_line(node)

        # 提取类的文档字符串
        docstring = ast.get_docstring(node) or ""

        # 创建组件
        component = CodeComponent(
            name=node.name,
            type="class",
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            description=docstring,
            dependencies=self._extract_dependencies(node),
            complexity_score=self._calculate_complexity(node),
            reusability_score=self._evaluate_reusability(node, file_path),
        )
        component.associated_test_cases = self._associate_test_cases(component.name, file_path)
        return component

    def analyze_function(
        self, node: ast.FunctionDef, file_path: str, content: str
    ) -> CodeComponent:
        """分析函数定义"""
        # 获取函数的行范围
        line_start = node.lineno
        line_end = self._get_node_end_line(node)

        # 提取函数的文档字符串
        docstring = ast.get_docstring(node) or ""

        # 创建组件
        component = CodeComponent(
            name=node.name,
            type="function",
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            description=docstring,
            dependencies=self._extract_dependencies(node),
            complexity_score=self._calculate_complexity(node),
            reusability_score=self._evaluate_reusability(node, file_path),
        )
        component.associated_test_cases = self._associate_test_cases(component.name, file_path)
        return component

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算代码复杂度"""
        complexity = 1

        # 遍历AST节点
        for child in ast.walk(node):
            # 控制流语句增加复杂度
            if isinstance(
                child,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.Try,
                    ast.ExceptHandler,
                    ast.With,
                    ast.AsyncWith,
                    ast.AsyncFor,
                ),
            ):
                complexity += 1
            # 布尔运算增加复杂度
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        # 根据复杂度评分
        if complexity <= 5:
            return 1  # 简单
        elif complexity <= 10:
            return 2  # 中等
        else:
            return 3  # 复杂

    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        """提取依赖"""
        dependencies = []

        # 遍历AST节点
        for child in ast.walk(node):
            # 导入语句
            if isinstance(child, ast.Import):
                for name in child.names:
                    dependencies.append(name.name)
            # from ... import 语句
            elif isinstance(child, ast.ImportFrom):
                if child.module:
                    for name in child.names:
                        dependencies.append(f"{child.module}.{name.name}")

        return list(set(dependencies))

    def _evaluate_reusability(self, node: ast.AST, file_path: str) -> float:
        """评估可复用性"""
        score = 1.0

        # 检查文档字符串
        # 确保node是FunctionDef, AsyncFunctionDef, ClassDef, 或 Module类型
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            docstring = ast.get_docstring(node)
            if not docstring:
                score -= 0.2
            elif len(docstring) < 50:
                score -= 0.1

        # 检查参数和返回值注解
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.returns:
                score -= 0.1
            for arg in node.args.args:
                if not arg.annotation:
                    score -= 0.05

        # 检查依赖数量
        dependencies = self._extract_dependencies(node)
        if len(dependencies) > 10:
            score -= 0.2
        elif len(dependencies) > 5:
            score -= 0.1

        # 检查复杂度
        complexity = self._calculate_complexity(node)
        if complexity == 3:
            score -= 0.3
        elif complexity == 2:
            score -= 0.1

        # 确保分数在0.0-1.0之间
        return max(0.0, min(1.0, score))

    def _get_node_end_line(self, node: ast.AST) -> int:
        """获取节点的结束行号"""
        # 优先使用end_lineno属性
        if hasattr(node, "end_lineno") and node.end_lineno is not None:
            return node.end_lineno

        # 如果没有end_lineno属性，遍历子节点找到最大行号
        max_lineno = getattr(node, "lineno", 0) # 使用getattr安全访问lineno
        for child in ast.walk(node):
            if hasattr(child, "lineno") and child.lineno is not None:
                max_lineno = max(max_lineno, child.lineno)
            if hasattr(child, "end_lineno") and child.end_lineno is not None:
                max_lineno = max(max_lineno, child.end_lineno)
        return max_lineno

    def _associate_test_cases(self, component_name: str, file_path: str) -> List[str]:
        """
        根据组件名称和文件路径，模拟关联测试用例。
        实际实现中，这里会查询测试用例管理系统或扫描测试文件。
        """
        associated_tests = []
        # 模拟逻辑：如果组件名包含“用户”或“管理”，则关联通用测试用例
        if "user" in component_name.lower() or "用户" in component_name:
            associated_tests.append("test_user_authentication")
            associated_tests.append("test_user_profile_management")
        if "manage" in component_name.lower() or "管理" in component_name:
            associated_tests.append("test_admin_dashboard")
            associated_tests.append("test_data_integrity")

        # 模拟逻辑：根据文件路径关联特定测试用例
        if "api" in file_path:
            associated_tests.append(f"test_api_{component_name}")
        if "service" in file_path:
            associated_tests.append(f"test_service_{component_name}")

        # 确保返回唯一值
        return list(set(associated_tests))

    def analyze_change_impact(self, changed_component_name: str, all_components: List[CodeComponent]) -> Dict[str, Any]:
        """
        分析代码变更的影响范围。
        这是一种初步的、基于依赖关系的变更影响分析。
        """
        impact_analysis = {
            "changed_component": changed_component_name,
            "direct_dependents": [],
            "indirect_dependents": [],
            "affected_test_cases": [],
            "potential_risks": [],
            "recommendations": [],
        }

        changed_component = next((c for c in all_components if c.name == changed_component_name), None)

        if not changed_component:
            impact_analysis["potential_risks"].append(f"未找到组件 '{changed_component_name}'，无法进行影响分析。")
            return impact_analysis

        # 1. 识别直接依赖者
        direct_dependents = []
        for component in all_components:
            if changed_component.name in component.dependencies:
                direct_dependents.append(component.name)
        impact_analysis["direct_dependents"] = direct_dependents

        # 2. 识别间接依赖者 (通过广度优先搜索或递归)
        indirect_dependents = set()
        queue = list(direct_dependents)
        visited = set(direct_dependents)

        while queue:
            current_dependent = queue.pop(0)
            for component in all_components:
                if current_dependent in component.dependencies and component.name not in visited:
                    indirect_dependents.add(component.name)
                    visited.add(component.name)
                    queue.append(component.name)
        impact_analysis["indirect_dependents"] = list(indirect_dependents)

        # 3. 识别受影响的测试用例
        affected_test_cases = set()
        if changed_component.associated_test_cases:
            affected_test_cases.update(changed_component.associated_test_cases)
        for dependent_name in direct_dependents + list(indirect_dependents):
            dependent_component = next((c for c in all_components if c.name == dependent_name), None)
            if dependent_component and dependent_component.associated_test_cases:
                affected_test_cases.update(dependent_component.associated_test_cases)
        impact_analysis["affected_test_cases"] = list(affected_test_cases)

        # 4. 评估潜在风险和建议
        if len(impact_analysis["direct_dependents"]) > 5 or len(impact_analysis["indirect_dependents"]) > 10:
            impact_analysis["potential_risks"].append("变更影响范围较大，可能引入回归问题。")
            impact_analysis["recommendations"].append("建议进行全面的回归测试和代码审查。")

        if not impact_analysis["affected_test_cases"]:
            impact_analysis["potential_risks"].append("未找到关联测试用例，变更风险较高。")
            impact_analysis["recommendations"].append("建议为受影响的功能编写新的测试用例。")

        if changed_component.complexity_score == 3: # 复杂组件
            impact_analysis["potential_risks"].append("修改复杂组件，可能引入新的复杂性或缺陷。")
            impact_analysis["recommendations"].append("建议进行详细的设计评审和单元测试。")

        return impact_analysis
