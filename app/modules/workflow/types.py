"""
智能流程编排核心数据类型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """节点类型"""

    START = "start"  # 开始节点
    END = "end"  # 结束节点
    TASK = "task"  # 任务节点
    DECISION = "decision"  # 决策节点
    PARALLEL = "parallel"  # 并行节点
    MERGE = "merge"  # 合并节点
    CONDITION = "condition"  # 条件节点
    AGENT = "agent"  # 智能体节点
    HUMAN = "human"  # 人工节点


class EdgeType(str, Enum):
    """边类型"""

    SEQUENTIAL = "sequential"  # 顺序执行
    CONDITIONAL = "conditional"  # 条件执行
    PARALLEL = "parallel"  # 并行执行
    FALLBACK = "fallback"  # 降级执行


class WorkflowState(str, Enum):
    """工作流状态"""

    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class ExecutionStrategy(str, Enum):
    """执行策略"""

    SEQUENTIAL = "sequential"  # 串行执行
    PARALLEL = "parallel"  # 并行执行
    ADAPTIVE = "adaptive"  # 自适应执行


class WorkflowCondition(BaseModel):
    """工作流条件"""

    id: str = Field(..., description="条件唯一标识")
    name: str = Field(..., description="条件名称")
    expression: str = Field(..., description="条件表达式")

    # 条件参数
    parameters: Dict[str, Any] = Field(default_factory=dict, description="条件参数")
    expected_value: Any = Field(None, description="期望值")
    operator: str = Field(default="==", description="比较操作符")

    # 条件元数据
    description: str = Field(default="", description="条件描述")
    priority: int = Field(default=0, description="条件优先级")

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """评估条件是否满足"""
        # 简化实现，实际应支持复杂表达式解析
        try:
            # 基于表达式和上下文评估条件
            return self._evaluate_expression(context)
        except Exception:
            return False

    def _evaluate_expression(self, context: Dict[str, Any]) -> bool:
        """评估表达式"""
        # 实际实现应该使用安全的表达式解析器
        return True  # 简化实现


class WorkflowNode(BaseModel):
    """工作流节点"""

    id: str = Field(..., description="节点唯一标识")
    name: str = Field(..., description="节点名称")
    type: NodeType = Field(..., description="节点类型")

    # 节点配置
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="节点参数")

    # 执行配置
    agent_name: Optional[str] = Field(None, description="关联的智能体名称")
    function_name: Optional[str] = Field(None, description="执行函数名称")
    timeout: int = Field(default=300, description="超时时间(秒)")
    retry_count: int = Field(default=0, description="重试次数")

    # 条件配置
    preconditions: List[WorkflowCondition] = Field(
        default_factory=list, description="前置条件"
    )
    postconditions: List[WorkflowCondition] = Field(
        default_factory=list, description="后置条件"
    )

    # 并行配置
    is_parallel: bool = Field(default=False, description="是否支持并行")
    parallel_group: Optional[str] = Field(None, description="并行组标识")

    # 状态信息
    state: WorkflowState = Field(default=WorkflowState.PENDING, description="节点状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

    # 结果信息
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")

    # 元数据
    description: str = Field(default="", description="节点描述")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class WorkflowEdge(BaseModel):
    """工作流边（连接）"""

    id: str = Field(..., description="边唯一标识")
    source_node_id: str = Field(..., description="源节点ID")
    target_node_id: str = Field(..., description="目标节点ID")
    type: EdgeType = Field(default=EdgeType.SEQUENTIAL, description="边类型")

    # 条件配置
    conditions: List[WorkflowCondition] = Field(
        default_factory=list, description="执行条件"
    )

    # 权重和优先级
    weight: float = Field(default=1.0, description="边权重")
    priority: int = Field(default=0, description="优先级")

    # 元数据
    name: str = Field(default="", description="边名称")
    description: str = Field(default="", description="边描述")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class WorkflowDefinition(BaseModel):
    """工作流定义"""

    id: str = Field(..., description="工作流唯一标识")
    name: str = Field(..., description="工作流名称")
    version: str = Field(default="1.0.0", description="版本号")

    # 节点和边
    nodes: List[WorkflowNode] = Field(..., description="节点列表")
    edges: List[WorkflowEdge] = Field(..., description="边列表")

    # 执行配置
    strategy: ExecutionStrategy = Field(
        default=ExecutionStrategy.ADAPTIVE, description="执行策略"
    )
    max_execution_time: int = Field(default=3600, description="最大执行时间(秒)")
    enable_rollback: bool = Field(default=True, description="是否启用回滚")

    # 监控配置
    enable_monitoring: bool = Field(default=True, description="是否启用监控")
    checkpoint_frequency: int = Field(default=10, description="检查点频率")

    # 元数据
    description: str = Field(default="", description="工作流描述")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class ExecutionContext(BaseModel):
    """执行上下文"""

    workflow_id: str = Field(..., description="工作流ID")
    execution_id: str = Field(..., description="执行ID")

    # 上下文数据
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="输出数据")

    # 执行状态
    current_node_id: Optional[str] = Field(None, description="当前节点ID")
    completed_nodes: List[str] = Field(default_factory=list, description="已完成节点")
    failed_nodes: List[str] = Field(default_factory=list, description="失败节点")

    # 时间信息
    start_time: datetime = Field(default_factory=datetime.now)
    last_update_time: datetime = Field(default_factory=datetime.now)

    # 扩展数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class ExecutionResult(BaseModel):
    """执行结果"""

    execution_id: str = Field(..., description="执行ID")
    workflow_id: str = Field(..., description="工作流ID")

    # 执行状态
    state: WorkflowState = Field(..., description="最终状态")
    success: bool = Field(..., description="是否成功")

    # 结果数据
    outputs: Dict[str, Any] = Field(default_factory=dict, description="输出数据")
    intermediate_results: Dict[str, Any] = Field(
        default_factory=dict, description="中间结果"
    )

    # 执行统计
    total_nodes: int = Field(..., description="总节点数")
    completed_nodes: int = Field(..., description="完成节点数")
    failed_nodes: int = Field(..., description="失败节点数")

    # 时间统计
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    duration: float = Field(..., description="执行时长(秒)")

    # 错误信息
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class WorkflowTemplate(BaseModel):
    """工作流模板"""

    id: str = Field(..., description="模板唯一标识")
    name: str = Field(..., description="模板名称")
    category: str = Field(..., description="模板分类")

    # 模板配置
    workflow_definition: WorkflowDefinition = Field(..., description="工作流定义")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模板参数")

    # 适用性
    use_cases: List[str] = Field(default_factory=list, description="适用场景")
    prerequisites: List[str] = Field(default_factory=list, description="前置条件")

    # 质量信息
    success_rate: float = Field(default=0.0, description="成功率")
    avg_duration: float = Field(default=0.0, description="平均执行时长")
    usage_count: int = Field(default=0, description="使用次数")

    # 元数据
    description: str = Field(default="", description="模板描述")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
