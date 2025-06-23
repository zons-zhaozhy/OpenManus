"""
架构设计助手流程 - 基于BaseFlow的多智能体协作
"""

from typing import Dict, List, Optional

from pydantic import Field

from app.flow.base import BaseFlow
from app.logger import logger

from .agents.architecture_reviewer import ArchitectureReviewerAgent
from .agents.database_designer import DatabaseDesignerAgent
from .agents.system_architect import SystemArchitectAgent
from .agents.tech_selector import TechSelectorAgent


class ArchitectureFlow(BaseFlow):
    """架构设计助手流程"""

    # 正确定义Pydantic字段
    current_context: Dict = Field(default_factory=dict)
    tech_selection_complete: bool = Field(default=False)
    architecture_design_complete: bool = Field(default=False)
    database_design_complete: bool = Field(default=False)

    def __init__(self, **kwargs):
        # 创建架构设计智能体团队
        agents = {
            "tech_selector": TechSelectorAgent(
                name="技术选型师", description="负责技术栈选择和分析"
            ),
            "architect": SystemArchitectAgent(
                name="系统架构师", description="负责系统架构设计"
            ),
            "db_designer": DatabaseDesignerAgent(
                name="数据库设计师", description="负责数据库架构设计"
            ),
            "reviewer": ArchitectureReviewerAgent(
                name="架构评审师", description="负责架构质量评审"
            ),
        }

        # 设置主要智能体为技术选型师
        super().__init__(agents=agents, primary_agent_key="tech_selector", **kwargs)

        # 明确初始化字段
        if not hasattr(self, "current_context"):
            self.current_context = {}
        if not hasattr(self, "tech_selection_complete"):
            self.tech_selection_complete = False
        if not hasattr(self, "architecture_design_complete"):
            self.architecture_design_complete = False
        if not hasattr(self, "database_design_complete"):
            self.database_design_complete = False

    async def execute(self, requirements_doc: str) -> str:
        """执行架构设计流程"""
        logger.info("开始架构设计流程")

        try:
            # 阶段1：技术选型
            tech_selection_result = await self._select_technology_stack(
                requirements_doc
            )

            # 阶段2：系统架构设计
            architecture_result = await self._design_system_architecture(
                requirements_doc, tech_selection_result
            )

            # 阶段3：数据库设计
            database_result = await self._design_database_schema(
                requirements_doc, architecture_result
            )

            # 阶段4：架构评审
            review_result = await self._review_architecture(
                tech_selection_result, architecture_result, database_result
            )

            return review_result

        except Exception as e:
            logger.error(f"架构设计流程执行失败: {e}")
            return f"架构设计过程中发生错误: {str(e)}"

    async def _select_technology_stack(self, requirements_doc: str) -> str:
        """技术选型阶段"""
        tech_selector = self.get_agent("tech_selector")

        # 执行技术选型
        result = await tech_selector.analyze_tech_requirements(requirements_doc)

        self.current_context["tech_selection"] = result
        self.tech_selection_complete = True

        logger.info("技术选型阶段完成")
        return result

    async def _design_system_architecture(
        self, requirements_doc: str, tech_stack: str
    ) -> str:
        """系统架构设计阶段"""
        architect = self.get_agent("architect")

        # 执行架构设计
        result = await architect.design_system_architecture(
            requirements_doc, tech_stack
        )

        self.current_context["architecture"] = result
        self.architecture_design_complete = True

        logger.info("系统架构设计阶段完成")
        return result

    async def _design_database_schema(
        self, requirements_doc: str, architecture_doc: str
    ) -> str:
        """数据库设计阶段"""
        db_designer = self.get_agent("db_designer")

        # 执行数据库设计
        result = await db_designer.design_database_schema(
            requirements_doc, architecture_doc
        )

        self.current_context["database"] = result
        self.database_design_complete = True

        logger.info("数据库设计阶段完成")
        return result

    async def _review_architecture(
        self, tech_stack: str, architecture_doc: str, database_doc: str
    ) -> str:
        """架构评审阶段"""
        reviewer = self.get_agent("reviewer")

        # 执行架构评审
        review_result = await reviewer.review_architecture(
            tech_stack, architecture_doc, database_doc
        )

        self.current_context["review"] = review_result

        # 检查评审结果
        review_summary = reviewer.get_review_summary()

        if review_summary["total_score"] >= 70:
            logger.info("架构评审通过，设计完成")
            return f"""# 架构设计完成报告

## 技术选型结果
{tech_stack}

## 系统架构设计
{architecture_doc}

## 数据库设计
{database_doc}

## 架构评审结果
{review_result}

**评审状态**: ✅ 通过 (得分: {review_summary['total_score']}/100)
**质量等级**: {review_summary['quality_level']}
**建议**: 可以进入编码实现阶段"""
        else:
            logger.warning("架构评审未通过，需要改进")
            return f"""# 架构设计需要改进

## 当前设计
- **技术选型**: {tech_stack[:200]}...
- **系统架构**: {architecture_doc[:200]}...
- **数据库设计**: {database_doc[:200]}...

## 评审意见
{review_result}

**评审状态**: ❌ 需改进 (得分: {review_summary['total_score']}/100)
**质量等级**: {review_summary['quality_level']}

请根据评审意见进行改进后重新提交。"""

    def get_progress(self) -> Dict:
        """获取流程进度"""
        return {
            "tech_selection_complete": self.tech_selection_complete,
            "architecture_design_complete": self.architecture_design_complete,
            "database_design_complete": self.database_design_complete,
            "current_stage": self._get_current_stage(),
            "context": self.current_context,
        }

    def _get_current_stage(self) -> str:
        """获取当前阶段"""
        if not self.tech_selection_complete:
            return "技术选型"
        elif not self.architecture_design_complete:
            return "系统架构设计"
        elif not self.database_design_complete:
            return "数据库设计"
        else:
            return "架构评审"
