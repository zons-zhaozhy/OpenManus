"""
工作流定义

提供工作流的基本定义和管理功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.logger import logger

from .workflow_error import WorkflowError
from .workflow_step import WorkflowStep


class StepDependency(BaseModel):
    """步骤依赖定义"""

    from_step: str = Field(..., description="源步骤")
    to_step: str = Field(..., description="目标步骤")
    condition: Optional[str] = Field(None, description="转换条件")


class WorkflowDefinition(BaseModel):
    """工作流定义"""

    id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: str = Field(..., description="工作流描述")
    version: str = Field(..., description="工作流版本")
    steps: List[WorkflowStep] = Field(default_factory=list, description="工作流步骤")
    dependencies: Dict[str, List[str]] = Field(
        default_factory=dict, description="步骤依赖"
    )
    initial_inputs: List[str] = Field(default_factory=list, description="初始输入")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    def validate(self) -> None:
        """验证工作流定义的有效性"""
        try:
            # 1. 验证步骤唯一性
            step_names = set()
            for step in self.steps:
                if step.name in step_names:
                    raise WorkflowError(f"存在重复的步骤名称: {step.name}")
                step_names.add(step.name)

            # 2. 验证依赖的有效性
            for step_name, deps in self.dependencies.items():
                if step_name not in step_names:
                    raise WorkflowError(f"步骤 {step_name} 不存在")
                for dep in deps:
                    if dep not in step_names:
                        raise WorkflowError(f"步骤 {step_name} 依赖的步骤 {dep} 不存在")

            # 3. 检查循环依赖
            self.validate_dependencies()

            # 4. 验证输入输出的连接性
            self._validate_io_connections()

            logger.info(f"工作流 {self.name} (ID: {self.id}) 验证通过")

        except Exception as e:
            logger.error(f"工作流验证失败: {e}")
            raise WorkflowError(f"工作流验证失败: {str(e)}")

    def validate_dependencies(self) -> bool:
        """验证步骤依赖的有效性"""
        # 检查所有步骤名称是否存在
        step_names = {step.name for step in self.steps}
        for from_step, to_steps in self.dependencies.items():
            if from_step not in step_names:
                return False
            for to_step in to_steps:
                if to_step not in step_names:
                    return False

        # 检查是否有循环依赖
        visited = set()
        path = set()

        def has_cycle(step: str) -> bool:
            visited.add(step)
            path.add(step)

            for next_step in self.dependencies.get(step, []):
                if next_step not in visited:
                    if has_cycle(next_step):
                        return True
                elif next_step in path:
                    return True

            path.remove(step)
            return False

        for step in step_names:
            if step not in visited:
                if has_cycle(step):
                    return False

        return True

    def _validate_io_connections(self) -> None:
        """验证步骤间的输入输出连接"""
        available_outputs = set(self.initial_inputs)

        # 按依赖顺序验证每个步骤
        for step in self._get_ordered_steps():
            # 检查步骤的输入是否可用
            for input_name in step.required_inputs:
                if input_name not in available_outputs:
                    raise WorkflowError(
                        f"步骤 {step.name} 的输入 {input_name} 未被前置步骤提供"
                    )

            # 添加步骤的输出到可用输出集合
            available_outputs.update(step.outputs)

    def _get_ordered_steps(self) -> List[WorkflowStep]:
        """获取按依赖顺序排序的步骤列表"""
        # 构建依赖图
        graph: Dict[str, List[str]] = {step.name: [] for step in self.steps}
        in_degree: Dict[str, int] = {step.name: 0 for step in self.steps}

        for step_name, deps in self.dependencies.items():
            for dep in deps:
                graph[dep].append(step_name)
                in_degree[step_name] += 1

        # 拓扑排序
        queue = [step.name for step, count in in_degree.items() if count == 0]
        ordered_names = []

        while queue:
            current = queue.pop(0)
            ordered_names.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered_names) != len(self.steps):
            raise WorkflowError("无法确定步骤的执行顺序，可能存在循环依赖")

        # 转换回WorkflowStep对象
        name_to_step = {step.name: step for step in self.steps}
        return [name_to_step[name] for name in ordered_names]

    def get_parallel_steps(self, completed_steps: Set[str]) -> List[str]:
        """
        获取可以并行执行的步骤

        Args:
            completed_steps: 已完成的步骤集合

        Returns:
            List[str]: 可以并行执行的步骤名称列表
        """
        parallel_steps = []

        for step in self.steps:
            if step.name in completed_steps:
                continue

            # 检查步骤的所有依赖是否都已完成
            dependencies_met = True
            for dep in self.dependencies.get(step.name, []):
                if dep not in completed_steps:
                    dependencies_met = False
                    break

            if dependencies_met:
                parallel_steps.append(step.name)

        return parallel_steps

    def get_next_steps(
        self, current_step: Optional[str], completed_steps: Set[str]
    ) -> List[str]:
        """
        获取下一个可执行的步骤

        Args:
            current_step: 当前步骤名称
            completed_steps: 已完成的步骤集合

        Returns:
            List[str]: 下一个可执行的步骤名称列表
        """
        if not current_step:
            # 如果没有当前步骤，返回所有没有依赖的步骤
            return [
                step.name
                for step in self.steps
                if not self.dependencies.get(step.name)
                and step.name not in completed_steps
            ]

        # 获取当前步骤的所有后续步骤
        next_steps = []
        for step in self.steps:
            if step.name in completed_steps:
                continue

            # 检查步骤的依赖是否都已完成
            dependencies = self.dependencies.get(step.name, [])
            if not dependencies:
                continue

            if current_step in dependencies:
                # 检查其他依赖是否都已完成
                other_deps_met = True
                for dep in dependencies:
                    if dep != current_step and dep not in completed_steps:
                        other_deps_met = False
                        break

                if other_deps_met:
                    next_steps.append(step.name)

        return next_steps

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [step.dict() for step in self.steps],
            "dependencies": self.dependencies,
            "initial_inputs": self.initial_inputs,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def update_metadata(self, key: str, value: Any) -> None:
        """更新元数据"""
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def add_step(self, step: WorkflowStep) -> None:
        """添加步骤"""
        self.steps.append(step)

    def add_dependency(self, from_step: str, to_step: str) -> None:
        """添加步骤依赖"""
        if from_step not in self.dependencies:
            self.dependencies[from_step] = []
        self.dependencies[from_step].append(to_step)

    def get_step_by_name(self, step_name: str) -> Optional[WorkflowStep]:
        """根据名称获取步骤"""
        for step in self.steps:
            if step.name == step_name:
                return step
        return None

    def get_step_dependencies(self, step_name: str) -> List[str]:
        """获取步骤的依赖"""
        return self.dependencies.get(step_name, [])

    def get_dependent_steps(self, step_name: str) -> List[str]:
        """获取依赖于指定步骤的步骤列表"""
        dependent_steps = []
        for from_step, to_steps in self.dependencies.items():
            if step_name in to_steps:
                dependent_steps.append(from_step)
        return dependent_steps

    def get_execution_order(self) -> List[str]:
        """获取步骤的执行顺序"""
        # 使用拓扑排序获取执行顺序
        ordered_steps = self._get_ordered_steps()
        return [step.name for step in ordered_steps]

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """转换为字典格式（兼容pydantic）"""
        d = super().dict(*args, **kwargs)
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d
