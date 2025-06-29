"""
代码模式识别器
"""

import ast
from typing import List, Optional

from app.logger import logger

from ..models.base import CodeComponent, CodePattern


class PatternRecognizer:
    """模式识别器"""

    def __init__(self, components: List[CodeComponent]):
        self.components = components
        self.patterns: List[CodePattern] = []

    def identify_patterns(self) -> List[CodePattern]:
        """识别所有模式"""
        self._identify_singleton_pattern()
        self._identify_factory_pattern()
        self._identify_observer_pattern()
        self._identify_strategy_pattern()
        return self.patterns

    def _identify_singleton_pattern(self):
        """识别单例模式"""
        for component in self.components:
            if component.type == "class":
                # 检查是否有私有构造函数和静态实例
                has_private_init = False
                has_static_instance = False
                has_get_instance = False

                for dep in component.dependencies:
                    if dep.endswith(".__init__"):
                        has_private_init = True
                    elif dep.endswith(".instance"):
                        has_static_instance = True
                    elif dep.endswith(".get_instance"):
                        has_get_instance = True

                if has_private_init and (has_static_instance or has_get_instance):
                    pattern = CodePattern(
                        name="Singleton",
                        pattern_type="design_pattern",
                        description="单例模式确保一个类只有一个实例，并提供一个全局访问点。",
                        files=[component.file_path],
                        usage_examples=[f"在{component.name}中实现"],
                        benefits=[
                            "确保类只有一个实例",
                            "提供全局访问点",
                            "控制并发访问共享资源",
                        ],
                    )
                    self.patterns.append(pattern)

    def _identify_factory_pattern(self):
        """识别工厂模式"""
        for component in self.components:
            if component.type == "class" and (
                "Factory" in component.name
                or any("create" in dep.lower() for dep in component.dependencies)
            ):
                pattern = CodePattern(
                    name="Factory",
                    pattern_type="design_pattern",
                    description="工厂模式用于创建对象而不暴露创建逻辑。",
                    files=[component.file_path],
                    usage_examples=[f"在{component.name}中实现"],
                    benefits=[
                        "封装对象创建逻辑",
                        "提供统一的创建接口",
                        "支持产品族的扩展",
                    ],
                )
                self.patterns.append(pattern)

    def _identify_observer_pattern(self):
        """识别观察者模式"""
        for component in self.components:
            if component.type == "class" and (
                any(
                    method in dep.lower()
                    for dep in component.dependencies
                    for method in ["notify", "subscribe", "observer"]
                )
            ):
                pattern = CodePattern(
                    name="Observer",
                    pattern_type="design_pattern",
                    description="观察者模式定义了对象之间的一对多依赖关系。",
                    files=[component.file_path],
                    usage_examples=[f"在{component.name}中实现"],
                    benefits=[
                        "支持松耦合设计",
                        "实现一对多的依赖关系",
                        "支持事件驱动编程",
                    ],
                )
                self.patterns.append(pattern)

    def _identify_strategy_pattern(self):
        """识别策略模式"""
        for component in self.components:
            if component.type == "class" and (
                "Strategy" in component.name
                or any(
                    "algorithm" in dep.lower() or "strategy" in dep.lower()
                    for dep in component.dependencies
                )
            ):
                pattern = CodePattern(
                    name="Strategy",
                    pattern_type="design_pattern",
                    description="策略模式定义了算法族，分别封装起来，让它们之间可以互相替换。",
                    files=[component.file_path],
                    usage_examples=[f"在{component.name}中实现"],
                    benefits=[
                        "算法可以自由切换",
                        "避免使用多重条件判断",
                        "扩展性良好",
                    ],
                )
                self.patterns.append(pattern)
