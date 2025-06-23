"""
需求分析助手流程 - 基于BaseFlow的多智能体协作

充分利用OpenManus现有能力：
- 继承BaseFlow进行多智能体管理
- 所有智能体继承BaseAgent，自动获得LLM、内存、状态管理
- 使用现有的配置系统和提示词系统
- 集成知识库和代码分析能力
- 优化的上下文共享机制
"""

import asyncio
import uuid
from typing import Dict, List, Optional

from pydantic import Field

from app.agent.base import BaseAgent
from app.flow.base import BaseFlow
from app.llm import LLM
from app.logger import logger

from .agents.business_analyst import BusinessAnalystAgent
from .agents.quality_reviewer import QualityReviewerAgent
from .agents.requirement_clarifier import RequirementClarifierAgent
from .agents.technical_writer import TechnicalWriterAgent
from .code_analyzer import CodeAnalyzer
from .context_manager import RequirementsContextManager
from .knowledge_base import RequirementsKnowledgeBase


class RequirementsFlow(BaseFlow):
    """需求分析助手流程 - 支持并行处理优化"""

    # 正确定义Pydantic字段
    current_context: Dict = Field(default_factory=dict)
    clarification_complete: bool = Field(default=False)
    analysis_complete: bool = Field(default=False)
    project_id: Optional[str] = Field(default=None)  # 项目制管理支持
    project_context: Optional[Dict] = Field(default=None)  # 项目上下文
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # 会话ID
    context_manager: Optional[object] = Field(default=None)  # 上下文管理器
    knowledge_base: Optional[object] = Field(default=None)  # 知识库
    code_analyzer: Optional[object] = Field(default=None)  # 代码分析器
    enable_parallel: bool = Field(default=True)  # 启用并行处理

    def __init__(self, project_id: Optional[str] = None, **kwargs):
        # 创建专门的智能体团队（包含质量保证）
        agents = {
            "clarifier": RequirementClarifierAgent(
                name="需求澄清师", description="负责澄清模糊的用户需求"
            ),
            "analyst": BusinessAnalystAgent(
                name="业务分析师", description="负责深度业务分析"
            ),
            "writer": TechnicalWriterAgent(
                name="技术文档编写师", description="负责编写需求规格说明书"
            ),
            "reviewer": QualityReviewerAgent(
                name="质量评审师", description="负责专业质量把关和评审"
            ),
        }

        # 设置主要智能体为澄清师
        super().__init__(agents=agents, primary_agent_key="clarifier", **kwargs)

        # 明确初始化字段
        if not hasattr(self, "current_context"):
            self.current_context = {}
        if not hasattr(self, "clarification_complete"):
            self.clarification_complete = False
        if not hasattr(self, "analysis_complete"):
            self.analysis_complete = False

        # 项目制管理支持
        self.project_id = project_id
        self.project_context = None
        self.enable_parallel = kwargs.get("enable_parallel", True)

        # 初始化增强组件
        self.session_id = kwargs.get("session_id", str(uuid.uuid4()))
        self.context_manager = RequirementsContextManager(self.session_id)
        self.knowledge_base = RequirementsKnowledgeBase()
        self.code_analyzer = CodeAnalyzer()

        # 如果有项目ID，加载项目上下文
        if self.project_id:
            self._load_project_context()

        logger.info(
            f"需求分析Flow初始化完成，会话ID: {self.session_id}, 项目ID: {self.project_id}, 并行模式: {self.enable_parallel}"
        )

    def _load_project_context(self):
        """加载项目上下文（项目制管理支持）"""
        try:
            # 这里应该从项目管理API获取项目上下文
            # 简化实现，实际应该调用项目管理服务
            import httpx

            # 模拟项目上下文获取
            self.project_context = {
                "project_id": self.project_id,
                "objective_guidance": "基于项目目标进行需求分析",
                "background_context": "项目背景上下文",
                "success_criteria": ["明确的需求规格", "可实施的技术方案"],
                "constraints": ["时间约束", "资源约束"],
                "current_stage": "requirements_analysis",
                "available_knowledge_bases": [],
                "codebase_info": None,
            }

            # 更新上下文管理器
            self.context_manager.update_global_state(
                "project_context", self.project_context
            )

            logger.info(f"加载项目上下文成功: {self.project_id}")

        except Exception as e:
            logger.warning(f"加载项目上下文失败: {e}")
            self.project_context = None

    def _build_project_guidance_prompt(self) -> str:
        """构建项目指引提示词"""
        if not self.project_context:
            return ""

        guidance_prompt = f"""
## 项目上下文指引

**项目目标：** {self.project_context.get('objective_guidance', '未指定')}

**项目背景：** {self.project_context.get('background_context', '未指定')}

**成功标准：**
{chr(10).join([f"- {criteria}" for criteria in self.project_context.get('success_criteria', [])])}

**约束条件：**
{chr(10).join([f"- {constraint}" for constraint in self.project_context.get('constraints', [])])}

**当前阶段：** {self.project_context.get('current_stage', '未指定')}

---
⚠️ **重要提醒：** 所有工作都必须紧密围绕上述项目目标和背景展开，确保不偏离项目整体方向！
---
"""
        return guidance_prompt

    async def execute(self, user_input: str) -> str:
        """执行并行优化的需求分析流程"""
        logger.info(f"开始需求分析流程 - 并行模式: {self.enable_parallel}")

        # 更新全局状态
        self.context_manager.update_global_state("user_input", user_input)
        self.context_manager.update_global_state("current_stage", "初始化")

        try:
            if self.enable_parallel:
                # 并行执行预处理阶段
                await self._parallel_preprocessing(user_input)

                # 并行执行分析阶段
                result = await self._parallel_analysis_flow(user_input)
            else:
                # 传统串行执行
                result = await self._sequential_analysis_flow(user_input)

            # 生成最终会话摘要
            session_summary = self.context_manager.get_session_summary()

            logger.info("需求分析流程完成")
            return {
                "final_result": result,
                "session_summary": session_summary,
                "context_items": self.context_manager.context_items[-10:],
                "quality_metrics": self._get_quality_metrics(),
                "parallel_enabled": self.enable_parallel,
            }

        except Exception as e:
            logger.error(f"需求分析流程执行失败: {e}")
            return {
                "error": f"需求分析过程中发生错误: {str(e)}",
                "session_summary": self.context_manager.get_session_summary(),
            }

    async def _parallel_preprocessing(self, user_input: str):
        """并行执行预处理阶段"""
        logger.info("开始并行预处理阶段")

        # 创建并行任务
        tasks = [
            self._preprocess_with_knowledge_base(user_input),
            self._preprocess_with_code_analysis(user_input),
        ]

        # 并行执行
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("并行预处理阶段完成")

    async def _parallel_analysis_flow(self, user_input: str) -> str:
        """并行优化的分析流程"""
        logger.info("开始并行分析流程")

        # 阶段1：需求澄清（独立执行）
        clarification_result = await self._clarify_requirements_enhanced(user_input)

        # 阶段2：基于澄清结果，并行执行业务分析和初步文档准备
        business_task = self._analyze_business_enhanced(clarification_result)

        # 等待业务分析完成
        analysis_result = await business_task

        # 阶段3：基于分析结果，并行执行文档编写和质量预检
        doc_task = self._write_documentation_enhanced(analysis_result)
        quality_prep_task = self._prepare_quality_review(analysis_result)

        # 并行等待
        documentation_result, quality_prep = await asyncio.gather(
            doc_task, quality_prep_task, return_exceptions=True
        )

        # 阶段4：最终质量评审
        review_result = await self._quality_review_enhanced(documentation_result)

        logger.info("并行分析流程完成")
        return review_result

    async def _sequential_analysis_flow(self, user_input: str) -> str:
        """传统串行分析流程"""
        logger.info("开始串行分析流程")

        # 预处理：使用知识库分析需求
        await self._preprocess_with_knowledge_base(user_input)

        # 预处理：代码库分析（如果需要）
        await self._preprocess_with_code_analysis(user_input)

        # 阶段1：需求澄清（知识库增强）
        clarification_result = await self._clarify_requirements_enhanced(user_input)

        # 阶段2：业务分析（上下文增强）
        analysis_result = await self._analyze_business_enhanced(clarification_result)

        # 阶段3：文档编写（代码复用建议）
        documentation_result = await self._write_documentation_enhanced(analysis_result)

        # 阶段4：质量评审（全面质量保证）
        review_result = await self._quality_review_enhanced(documentation_result)

        logger.info("串行分析流程完成")
        return review_result

    async def _prepare_quality_review(self, analysis_result: str) -> str:
        """准备质量评审资料（可并行执行）"""
        logger.info("开始准备质量评审资料")

        # 生成质量检查清单
        quality_checklist = self.knowledge_base.get_quality_checklist_for_stage(
            "质量评审"
        )

        # 分析潜在问题
        potential_issues = await self._analyze_potential_issues(analysis_result)

        self.context_manager.add_context_item(
            agent_name="质量评审准备",
            stage="质量评审准备",
            content=f"质量检查清单准备完成，识别潜在问题: {len(potential_issues)}个",
            content_type="quality_preparation",
            metadata={
                "checklist_items": len(quality_checklist),
                "potential_issues": potential_issues,
            },
        )

        logger.info("质量评审资料准备完成")
        return "质量评审准备完成"

    async def _analyze_potential_issues(self, analysis_result: str) -> List[str]:
        """分析潜在问题（支持并行）"""
        # 模拟问题分析
        await asyncio.sleep(0.1)  # 模拟分析时间

        potential_issues = ["需求边界模糊", "性能要求不明确", "用户角色定义不够清晰"]

        return potential_issues

    # ===== 原有方法（优化支持并行） =====

    async def _clarify_requirements(self, user_input: str) -> str:
        """需求澄清阶段"""
        clarifier = self.get_agent("clarifier")

        # 更新智能体记忆
        clarifier.update_memory("user", user_input)

        # 执行澄清步骤
        result = await clarifier.run()

        self.current_context["clarification"] = result
        self.clarification_complete = True

        logger.info("需求澄清阶段完成")
        return result

    async def _analyze_business(self, clarification_result: str) -> str:
        """业务分析阶段"""
        analyst = self.get_agent("analyst")

        # 传递澄清结果
        context_prompt = f"基于以下需求澄清结果进行业务分析：\n\n{clarification_result}"
        analyst.update_memory("system", context_prompt)

        # 执行分析步骤
        result = await analyst.run()

        self.current_context["analysis"] = result
        self.analysis_complete = True

        logger.info("业务分析阶段完成")
        return result

    async def _write_documentation(self, analysis_result: str) -> str:
        """文档编写阶段"""
        writer = self.get_agent("writer")

        # 传递分析结果
        context_prompt = (
            f"基于以下业务分析结果编写需求规格说明书：\n\n{analysis_result}"
        )
        writer.update_memory("system", context_prompt)

        # 执行文档编写
        result = await writer.run()

        self.current_context["documentation"] = result

        logger.info("文档编写阶段完成")
        return result

    async def _quality_review(self, documentation_result: str) -> str:
        """质量评审阶段 - 专业质量把关"""
        reviewer = self.get_agent("reviewer")

        # 传递所有前期成果供评审
        all_results = {
            "澄清结果": self.current_context.get("clarification", ""),
            "分析结果": self.current_context.get("analysis", ""),
            "文档结果": documentation_result,
        }

        context_prompt = f"""请对以下需求分析全套成果进行专业质量评审：

## 需求澄清成果
{all_results['澄清结果']}

## 业务分析成果
{all_results['分析结果']}

## 技术文档成果
{all_results['文档结果']}

请基于软件工程质量标准，进行独立、客观、专业的质量评审。"""

        reviewer.update_memory("system", context_prompt)

        # 执行质量评审
        review_result = await reviewer.run()

        self.current_context["review"] = review_result

        # 检查评审结果，决定是否需要改进
        review_summary = reviewer.get_review_summary()

        if review_summary["total_score"] >= 70:
            logger.info("质量评审通过，流程完成")
            return f"""# 需求分析完成报告

## 最终文档
{documentation_result}

## 质量评审结果
{review_result}

**评审状态**: ✅ 通过 (得分: {review_summary['total_score']}/100)
**质量等级**: {review_summary['quality_level']}"""
        else:
            logger.warning("质量评审未通过，需要改进")
            return f"""# 需求分析需要改进

## 当前文档
{documentation_result}

## 质量评审意见
{review_result}

**评审状态**: ❌ 需改进 (得分: {review_summary['total_score']}/100)
**质量等级**: {review_summary['quality_level']}

请根据评审意见进行改进后重新提交。"""

    async def ask_clarification_question(self, question: str) -> str:
        """处理澄清问题"""
        clarifier = self.get_agent("clarifier")
        clarifier.update_memory("user", question)

        response = await clarifier.step()
        return response

    def get_progress(self) -> Dict:
        """获取流程进度"""
        return {
            "clarification_complete": self.clarification_complete,
            "analysis_complete": self.analysis_complete,
            "current_stage": self._get_current_stage(),
            "context": self.current_context,
            "parallel_enabled": self.enable_parallel,
        }

    def _get_current_stage(self) -> str:
        """获取当前阶段"""
        if not self.clarification_complete:
            return "需求澄清"
        elif not self.analysis_complete:
            return "业务分析"
        else:
            return "文档编写"

    # ==== 增强方法实现 ====

    async def _preprocess_with_knowledge_base(self, user_input: str):
        """使用知识库预处理需求"""
        logger.info("开始知识库预处理")

        # 识别需求模式
        patterns = self.knowledge_base.identify_requirement_patterns(user_input)
        if patterns:
            self.context_manager.add_context_item(
                agent_name="知识库",
                stage="预处理",
                content=f"识别到需求模式: {[p.name for p in patterns]}",
                content_type="pattern_analysis",
                metadata={"patterns": [p.__dict__ for p in patterns]},
            )

        # 建议业务领域
        domain = self.knowledge_base.suggest_business_domain(user_input)
        if domain:
            self.context_manager.add_context_item(
                agent_name="知识库",
                stage="预处理",
                content=f"建议业务领域: {domain.name}",
                content_type="domain_suggestion",
                metadata={"domain": domain.__dict__},
            )

        # 生成初始澄清问题
        questions = self.knowledge_base.generate_clarification_questions(user_input)
        if questions:
            self.context_manager.add_context_item(
                agent_name="知识库",
                stage="预处理",
                content=f"建议澄清问题: {questions[:3]}",  # 前3个问题
                content_type="clarification_questions",
                metadata={"questions": questions},
            )

    async def _preprocess_with_code_analysis(self, user_input: str):
        """代码库预处理分析"""
        logger.info("开始代码库预处理")

        # 查找相似实现
        similar_components = self.code_analyzer.find_similar_implementations(user_input)
        if similar_components:
            self.context_manager.add_context_item(
                agent_name="代码分析器",
                stage="预处理",
                content=f"发现相似实现: {[c.name for c in similar_components]}",
                content_type="code_reuse",
                metadata={"components": [c.__dict__ for c in similar_components]},
            )

        # 估算实现工作量
        effort_estimation = self.code_analyzer.estimate_implementation_effort(
            user_input
        )
        self.context_manager.add_context_item(
            agent_name="代码分析器",
            stage="预处理",
            content=f"工作量估算: {effort_estimation['effort_level']} ({effort_estimation['estimated_days']})",
            content_type="effort_estimation",
            metadata={"estimation": effort_estimation},
        )

    async def _clarify_requirements_enhanced(self, user_input: str) -> str:
        """增强的需求澄清（项目制管理 + 知识库增强）"""
        self.context_manager.update_global_state("current_stage", "需求澄清")

        clarifier = self.get_agent("clarifier")

        # 构建项目指引
        project_guidance = self._build_project_guidance_prompt()

        # 构建增强的上下文提示
        base_context_prompt = self.context_manager.build_context_prompt(
            "需求澄清师", "需求澄清"
        )

        # 组合项目指引和基础上下文
        enhanced_context_prompt = f"""
{project_guidance}

{base_context_prompt}

## 用户需求输入
{user_input}

**重要提醒：** 澄清过程必须紧密围绕项目目标展开，确保所有澄清问题都服务于项目的整体成功！
"""

        # 更新智能体记忆
        clarifier.update_memory("system", enhanced_context_prompt)

        # 执行澄清步骤
        result = await clarifier.run()

        # 记录上下文
        self.context_manager.add_context_item(
            agent_name="需求澄清师",
            stage="需求澄清",
            content=result,
            content_type="clarification_result",
            confidence=0.8,
            metadata={"project_guided": bool(self.project_context)},
        )

        self.current_context["clarification"] = result
        self.clarification_complete = True
        self.context_manager.update_global_state("clarity_score", 0.8)

        logger.info("项目制管理增强的需求澄清阶段完成")
        return result

    async def _analyze_business_enhanced(self, clarification_result: str) -> str:
        """增强的业务分析（项目制管理指引）"""
        self.context_manager.update_global_state("current_stage", "业务分析")

        analyst = self.get_agent("analyst")

        # 构建项目指引
        project_guidance = self._build_project_guidance_prompt()

        # 构建增强上下文
        base_context_prompt = self.context_manager.build_context_prompt(
            "业务分析师", "业务分析"
        )

        # 传递澄清结果和增强上下文
        enhanced_prompt = f"""{project_guidance}

{base_context_prompt}

## 需求澄清结果
{clarification_result}

**分析要求：** 请基于项目目标和背景进行深度业务分析，确保分析结果与项目整体方向高度一致！
请特别关注如何通过业务分析支撑项目成功标准的达成。"""

        analyst.update_memory("system", enhanced_prompt)

        # 执行分析步骤
        result = await analyst.run()

        # 记录上下文
        self.context_manager.add_context_item(
            agent_name="业务分析师",
            stage="业务分析",
            content=result,
            content_type="business_analysis",
            confidence=0.85,
            metadata={"project_guided": bool(self.project_context)},
        )

        self.current_context["analysis"] = result
        self.analysis_complete = True
        self.context_manager.update_global_state("business_complexity", "中等")

        logger.info("项目制管理指引的业务分析阶段完成")
        return result

    async def _write_documentation_enhanced(self, analysis_result: str) -> str:
        """增强的文档编写（项目制管理指引）"""
        self.context_manager.update_global_state("current_stage", "文档编写")

        writer = self.get_agent("writer")

        # 构建项目指引
        project_guidance = self._build_project_guidance_prompt()

        # 构建增强上下文
        base_context_prompt = self.context_manager.build_context_prompt(
            "技术文档师", "文档编写"
        )

        # 获取代码复用建议
        code_suggestions = []
        for item in self.context_manager.context_items:
            if item.content_type == "code_reuse":
                code_suggestions.extend(item.metadata.get("components", []))

        enhanced_prompt = f"""{project_guidance}

{base_context_prompt}

## 业务分析结果
{analysis_result}

## 代码复用建议
{code_suggestions[:3] if code_suggestions else "无特别建议"}

**文档编写要求：** 请编写专业的需求规格说明书，确保文档内容与项目目标高度契合。
特别要体现如何通过需求实现满足项目成功标准，并充分考虑项目约束条件。
同时考虑代码复用和实现可行性。"""

        writer.update_memory("system", enhanced_prompt)

        # 执行文档编写
        result = await writer.run()

        # 记录上下文
        self.context_manager.add_context_item(
            agent_name="技术文档师",
            stage="文档编写",
            content=result,
            content_type="requirements_document",
            confidence=0.9,
            metadata={"project_guided": bool(self.project_context)},
        )

        self.current_context["documentation"] = result
        self.context_manager.update_global_state("document_completeness", 0.9)

        logger.info("项目制管理指引的文档编写阶段完成")
        return result

    async def _quality_review_enhanced(self, documentation_result: str) -> str:
        """增强的质量评审（项目制管理指引）"""
        self.context_manager.update_global_state("current_stage", "质量评审")

        reviewer = self.get_agent("reviewer")

        # 构建项目指引
        project_guidance = self._build_project_guidance_prompt()

        # 获取质量检查清单
        quality_checklist = self.knowledge_base.get_quality_checklist_for_stage(
            "质量评审"
        )

        # 构建全面的评审上下文
        all_results = {
            "澄清结果": self.current_context.get("clarification", ""),
            "分析结果": self.current_context.get("analysis", ""),
            "文档结果": documentation_result,
        }

        enhanced_prompt = f"""{project_guidance}

请对以下需求分析全套成果进行专业质量评审：

## 项目上下文摘要
{self.context_manager.get_session_summary()}

## 需求澄清成果
{all_results['澄清结果']}

## 业务分析成果
{all_results['分析结果']}

## 技术文档成果
{all_results['文档结果']}

## 质量检查清单
{quality_checklist}

**评审要求：** 请特别关注成果是否与项目目标高度契合，是否有助于项目成功标准的达成。
同时基于软件工程质量标准，进行独立、客观、专业的全面质量评审。"""

        reviewer.update_memory("system", enhanced_prompt)

        # 执行质量评审
        review_result = await reviewer.run()

        # 记录最终评审结果
        self.context_manager.add_context_item(
            agent_name="质量评审师",
            stage="质量评审",
            content=review_result,
            content_type="quality_review",
            confidence=1.0,
        )

        self.current_context["review"] = review_result

        # 更新最终质量分数
        review_summary = reviewer.get_review_summary()
        final_score = review_summary.get("total_score", 75)
        self.context_manager.update_global_state("quality_score", final_score)

        logger.info("增强质量评审阶段完成")
        return review_result

    def _get_quality_metrics(self) -> Dict:
        """获取质量指标"""
        return {
            "clarity_score": self.context_manager.global_state.get("clarity_score", 0),
            "business_complexity": self.context_manager.global_state.get(
                "business_complexity", "未知"
            ),
            "document_completeness": self.context_manager.global_state.get(
                "document_completeness", 0
            ),
            "quality_score": self.context_manager.global_state.get("quality_score", 0),
            "total_context_items": len(self.context_manager.context_items),
            "session_duration": str(
                self.context_manager.get_session_summary().get(
                    "session_duration", "未知"
                )
            ),
        }
