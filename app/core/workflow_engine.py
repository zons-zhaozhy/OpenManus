"""
工作流引擎 - 软件开发生命周期工作流定义与执行

预定义的标准工作流：
1. 完整软件开发流程
2. 需求分析专项流程
3. 架构设计专项流程
4. 快速原型开发流程
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .multi_agent_alliance import AssistantRole, WorkItem


class WorkflowType(Enum):
    """工作流类型"""

    FULL_DEVELOPMENT = "full_development"  # 完整软件开发
    REQUIREMENTS_ONLY = "requirements_only"  # 仅需求分析
    ARCHITECTURE_ONLY = "architecture_only"  # 仅架构设计
    PROTOTYPE_DEVELOPMENT = "prototype_development"  # 快速原型
    MAINTENANCE = "maintenance"  # 系统维护


@dataclass
class WorkflowTemplate:
    """工作流模板"""

    name: str
    description: str
    work_items: List[WorkItem]
    estimated_duration: str
    required_inputs: List[str]
    expected_outputs: List[str]


class WorkflowEngine:
    """工作流引擎"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[WorkflowType, WorkflowTemplate]:
        """初始化工作流模板"""
        templates = {}

        # 完整软件开发流程
        templates[WorkflowType.FULL_DEVELOPMENT] = WorkflowTemplate(
            name="完整软件开发流程",
            description="从需求分析到部署的完整软件开发生命周期",
            work_items=[
                WorkItem(
                    name="需求澄清和分析",
                    from_assistant=AssistantRole.REQUIREMENTS,
                    to_assistant=AssistantRole.ARCHITECTURE,
                    description="澄清用户需求，生成详细需求规格说明书",
                    dependencies=[],
                    deliverables=["需求规格说明书", "用户故事", "验收标准"],
                ),
                WorkItem(
                    name="系统架构设计",
                    from_assistant=AssistantRole.ARCHITECTURE,
                    to_assistant=AssistantRole.DEVELOPMENT,
                    description="基于需求设计系统架构和技术方案",
                    dependencies=["需求澄清和分析"],
                    deliverables=["架构设计文档", "技术选型方案", "系统设计图"],
                ),
                WorkItem(
                    name="代码开发实现",
                    from_assistant=AssistantRole.DEVELOPMENT,
                    to_assistant=AssistantRole.TESTING,
                    description="根据架构设计实现系统功能",
                    dependencies=["系统架构设计"],
                    deliverables=["源代码", "开发文档", "API文档"],
                ),
                WorkItem(
                    name="系统测试验证",
                    from_assistant=AssistantRole.TESTING,
                    to_assistant=AssistantRole.DEPLOYMENT,
                    description="全面测试系统功能和性能",
                    dependencies=["代码开发实现"],
                    deliverables=["测试报告", "缺陷报告", "性能报告"],
                ),
                WorkItem(
                    name="系统部署发布",
                    from_assistant=AssistantRole.DEPLOYMENT,
                    to_assistant=None,
                    description="部署系统到生产环境",
                    dependencies=["系统测试验证"],
                    deliverables=["部署文档", "运维手册", "监控配置"],
                ),
            ],
            estimated_duration="2-4周",
            required_inputs=["用户需求描述", "项目目标", "技术约束"],
            expected_outputs=["完整可运行的软件系统", "全套技术文档"],
        )

        # 仅需求分析流程
        templates[WorkflowType.REQUIREMENTS_ONLY] = WorkflowTemplate(
            name="需求分析专项流程",
            description="专注于深度需求分析和澄清",
            work_items=[
                WorkItem(
                    name="初步需求收集",
                    from_assistant=AssistantRole.REQUIREMENTS,
                    to_assistant=AssistantRole.REQUIREMENTS,
                    description="收集和整理初始需求",
                    dependencies=[],
                    deliverables=["需求清单", "干系人分析"],
                ),
                WorkItem(
                    name="需求澄清对话",
                    from_assistant=AssistantRole.REQUIREMENTS,
                    to_assistant=AssistantRole.REQUIREMENTS,
                    description="通过多轮对话澄清模糊需求",
                    dependencies=["初步需求收集"],
                    deliverables=["澄清问题列表", "澄清结果记录"],
                ),
                WorkItem(
                    name="需求规格编写",
                    from_assistant=AssistantRole.REQUIREMENTS,
                    to_assistant=None,
                    description="编写正式的需求规格说明书",
                    dependencies=["需求澄清对话"],
                    deliverables=["需求规格说明书", "用户故事", "验收标准"],
                ),
            ],
            estimated_duration="3-7天",
            required_inputs=["项目背景", "基本需求描述"],
            expected_outputs=["详细需求规格说明书"],
        )

        # 快速原型开发流程
        templates[WorkflowType.PROTOTYPE_DEVELOPMENT] = WorkflowTemplate(
            name="快速原型开发流程",
            description="快速构建可演示的系统原型",
            work_items=[
                WorkItem(
                    name="核心需求识别",
                    from_assistant=AssistantRole.REQUIREMENTS,
                    to_assistant=AssistantRole.ARCHITECTURE,
                    description="识别原型必需的核心功能",
                    dependencies=[],
                    deliverables=["核心功能列表", "原型目标"],
                ),
                WorkItem(
                    name="原型架构设计",
                    from_assistant=AssistantRole.ARCHITECTURE,
                    to_assistant=AssistantRole.DEVELOPMENT,
                    description="设计轻量级的原型架构",
                    dependencies=["核心需求识别"],
                    deliverables=["原型架构图", "技术栈选择"],
                ),
                WorkItem(
                    name="原型快速开发",
                    from_assistant=AssistantRole.DEVELOPMENT,
                    to_assistant=AssistantRole.TESTING,
                    description="快速实现原型功能",
                    dependencies=["原型架构设计"],
                    deliverables=["原型代码", "演示界面"],
                ),
                WorkItem(
                    name="原型验证测试",
                    from_assistant=AssistantRole.TESTING,
                    to_assistant=None,
                    description="验证原型功能可用性",
                    dependencies=["原型快速开发"],
                    deliverables=["原型测试报告", "用户反馈"],
                ),
            ],
            estimated_duration="3-10天",
            required_inputs=["原型目标", "核心功能需求"],
            expected_outputs=["可演示的系统原型"],
        )

        return templates

    def get_workflow_template(
        self, workflow_type: WorkflowType
    ) -> Optional[WorkflowTemplate]:
        """获取工作流模板"""
        return self.templates.get(workflow_type)

    def list_available_workflows(self) -> List[Dict]:
        """列出可用的工作流程"""
        workflows = []
        for workflow_type, template in self.templates.items():
            workflows.append(
                {
                    "type": workflow_type.value,
                    "name": template.name,
                    "description": template.description,
                    "estimated_duration": template.estimated_duration,
                    "steps": len(template.work_items),
                    "required_inputs": template.required_inputs,
                    "expected_outputs": template.expected_outputs,
                }
            )
        return workflows

    def customize_workflow(
        self, base_type: WorkflowType, customizations: Dict
    ) -> WorkflowTemplate:
        """自定义工作流程"""
        base_template = self.templates[base_type]

        # 创建自定义模板（简化实现）
        custom_template = WorkflowTemplate(
            name=customizations.get("name", f"自定义_{base_template.name}"),
            description=customizations.get("description", base_template.description),
            work_items=base_template.work_items.copy(),  # 后续可支持更复杂的自定义
            estimated_duration=customizations.get(
                "estimated_duration", base_template.estimated_duration
            ),
            required_inputs=customizations.get(
                "required_inputs", base_template.required_inputs
            ),
            expected_outputs=customizations.get(
                "expected_outputs", base_template.expected_outputs
            ),
        )

        return custom_template

    def validate_workflow(self, template: WorkflowTemplate) -> Dict:
        """验证工作流程的有效性"""
        validation_result = {"valid": True, "errors": [], "warnings": []}

        # 检查依赖关系
        task_names = [item.name for item in template.work_items]

        for item in template.work_items:
            for dependency in item.dependencies:
                if dependency not in task_names:
                    validation_result["errors"].append(
                        f"任务 '{item.name}' 的依赖 '{dependency}' 不存在"
                    )
                    validation_result["valid"] = False

        # 检查循环依赖（简化实现）
        dependency_graph = {}
        for item in template.work_items:
            dependency_graph[item.name] = item.dependencies

        # 更多验证逻辑可以在这里添加

        return validation_result
