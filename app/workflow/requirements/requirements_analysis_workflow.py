"""
需求分析工作流定义

实现基于多智能体的需求分析流程，包括：
1. 初始需求分析
2. 需求澄清
3. 业务分析
4. 技术可行性分析
5. 质量审查
6. 文档生成
"""

from datetime import datetime
from typing import Dict, List, Optional

from ..core.workflow_definition import WorkflowDefinition
from ..core.workflow_step import WorkflowStep


class RequirementsAnalysisStep(WorkflowStep):
    """需求分析步骤基类"""

    def __init__(
        self,
        name: str,
        description: str,
        agent_type: str,
        required_inputs: List[str],
        outputs: List[str],
        timeout: int = 300,
        retries: int = 3,
    ):
        super().__init__(
            name=name,
            description=description,
            agent_type=agent_type,
            required_inputs=required_inputs,
            outputs=outputs,
            timeout=timeout,
            retries=retries,
        )


class InitialAnalysisStep(RequirementsAnalysisStep):
    """初始需求分析步骤"""

    def __init__(self):
        super().__init__(
            name="initial_analysis",
            description="对初始需求进行分析",
            agent_type="requirements_analyzer",
            required_inputs=["initial_requirements", "project_context"],
            outputs=[
                "initial_analysis_result",
                "requirement_points",
                "analysis_depth",
            ],
            timeout=300,
        )


class ClarificationStep(RequirementsAnalysisStep):
    """需求澄清步骤"""

    def __init__(self):
        super().__init__(
            name="clarification",
            description="通过提问澄清需求细节",
            agent_type="requirement_clarifier",
            required_inputs=["initial_analysis_result", "requirement_points"],
            outputs=["clarified_requirements", "clarification_questions"],
            timeout=300,
        )


class BusinessAnalysisStep(RequirementsAnalysisStep):
    """业务分析步骤"""

    def __init__(self):
        super().__init__(
            name="business_analysis",
            description="分析需求的业务价值和影响",
            agent_type="business_analyst",
            required_inputs=["clarified_requirements"],
            outputs=["business_analysis_result", "business_rules"],
            timeout=300,
        )


class TechnicalAnalysisStep(RequirementsAnalysisStep):
    """技术可行性分析步骤"""

    def __init__(self):
        super().__init__(
            name="technical_analysis",
            description="评估需求的技术可行性",
            agent_type="technical_analyst",
            required_inputs=["clarified_requirements", "business_rules"],
            outputs=["technical_analysis_result", "technical_constraints"],
            timeout=300,
        )


class QualityReviewStep(RequirementsAnalysisStep):
    """质量审查步骤"""

    def __init__(self):
        super().__init__(
            name="quality_review",
            description="审查需求的质量和完整性",
            agent_type="quality_reviewer",
            required_inputs=[
                "clarified_requirements",
                "business_analysis_result",
                "technical_analysis_result",
            ],
            outputs=["quality_review_result", "improvement_suggestions"],
            timeout=300,
        )


class DocumentationStep(RequirementsAnalysisStep):
    """文档生成步骤"""

    def __init__(self):
        super().__init__(
            name="documentation",
            description="生成需求规格说明文档",
            agent_type="technical_writer",
            required_inputs=[
                "clarified_requirements",
                "business_analysis_result",
                "technical_analysis_result",
                "quality_review_result",
            ],
            outputs=["requirements_document"],
            timeout=300,
        )


class RequirementsAnalysisWorkflow(WorkflowDefinition):
    """需求分析工作流"""

    def __init__(self, workflow_id: str):
        super().__init__(
            id=workflow_id,
            name="需求分析工作流",
            description="通过多智能体协作完成需求分析",
            version="1.0.0",
            initial_inputs=["initial_requirements", "project_context"],
        )

        # 创建步骤
        initial_analysis = InitialAnalysisStep()
        clarification = ClarificationStep()
        business_analysis = BusinessAnalysisStep()
        technical_analysis = TechnicalAnalysisStep()
        quality_review = QualityReviewStep()
        documentation = DocumentationStep()

        # 添加步骤
        self.add_step(initial_analysis)
        self.add_step(clarification)
        self.add_step(business_analysis)
        self.add_step(technical_analysis)
        self.add_step(quality_review)
        self.add_step(documentation)

        # 添加步骤依赖
        self.add_dependency("initial_analysis", "clarification")
        self.add_dependency("clarification", "business_analysis")
        self.add_dependency("clarification", "technical_analysis")  # 可以与业务分析并行
        self.add_dependency("business_analysis", "quality_review")
        self.add_dependency("technical_analysis", "quality_review")
        self.add_dependency("quality_review", "documentation")

        # 添加元数据
        self.metadata.update(
            {
                "max_clarification_rounds": 3,
                "supports_parallel_execution": True,
                "created_by": "system",
                "created_at": datetime.now().isoformat(),
            }
        )

    def get_clarification_step(self) -> Optional[ClarificationStep]:
        """获取需求澄清步骤"""
        for step in self.steps:
            if isinstance(step, ClarificationStep):
                return step
        return None

    def get_business_analysis_step(self) -> Optional[BusinessAnalysisStep]:
        """获取业务分析步骤"""
        for step in self.steps:
            if isinstance(step, BusinessAnalysisStep):
                return step
        return None

    def get_technical_analysis_step(self) -> Optional[TechnicalAnalysisStep]:
        """获取技术分析步骤"""
        for step in self.steps:
            if isinstance(step, TechnicalAnalysisStep):
                return step
        return None

    def get_quality_review_step(self) -> Optional[QualityReviewStep]:
        """获取质量审查步骤"""
        for step in self.steps:
            if isinstance(step, QualityReviewStep):
                return step
        return None

    def get_documentation_step(self) -> Optional[DocumentationStep]:
        """获取文档生成步骤"""
        for step in self.steps:
            if isinstance(step, DocumentationStep):
                return step
        return None
