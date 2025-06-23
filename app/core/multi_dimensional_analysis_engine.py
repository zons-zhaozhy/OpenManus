"""
多维度并行分析引擎
参考openmanus-desktop项目，实现多维度需求分析

分析维度：
1. 需求与整体目标的相关性和冲突性分析
2. 需求与知识库的相关性和冲突性分析
3. 需求与代码库的相关性和冲突性分析
4. 需求的专业分析（功能性、技术性、商业性）
5. 需求的风险评估和可行性分析
6. 需求的优先级和依赖关系分析
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.assistants.requirements.code_analyzer import CodeAnalyzer
from app.config import ConfigManager
from app.llm import LLM
from app.logger import logger
from app.modules.knowledge_base.service import KnowledgeBaseService


@dataclass
class AnalysisDimension:
    """分析维度定义"""

    name: str
    description: str
    priority: int  # 1-5优先级
    parallel_group: str  # 并行组标识
    depends_on: List[str]  # 依赖的其他维度


@dataclass
class DimensionResult:
    """维度分析结果"""

    dimension_name: str
    status: str  # success, failed, skipped
    result: Dict[str, Any]
    processing_time: float
    confidence: float
    warnings: List[str]
    conflicts: List[str]


class MultiDimensionalAnalysisEngine:
    """多维度并行分析引擎"""

    def __init__(self):
        self.config = ConfigManager()
        LLM.clear_instances()  # 清除旧实例
        self.llm = LLM()
        self.knowledge_base = KnowledgeBaseService()
        self.code_analyzer = CodeAnalyzer()

        # 定义分析维度
        self.dimensions = self._define_analysis_dimensions()
        logger.info(f"多维度分析引擎初始化完成，包含 {len(self.dimensions)} 个分析维度")

    def _define_analysis_dimensions(self) -> List[AnalysisDimension]:
        """定义分析维度"""
        return [
            AnalysisDimension(
                name="goal_alignment",
                description="需求与整体目标的相关性和冲突性分析",
                priority=5,
                parallel_group="alignment",
                depends_on=[],
            ),
            AnalysisDimension(
                name="knowledge_alignment",
                description="需求与知识库的相关性和冲突性分析",
                priority=4,
                parallel_group="alignment",
                depends_on=[],
            ),
            AnalysisDimension(
                name="codebase_alignment",
                description="需求与代码库的相关性和冲突性分析",
                priority=4,
                parallel_group="alignment",
                depends_on=[],
            ),
            AnalysisDimension(
                name="professional_analysis",
                description="需求的专业分析（功能性、技术性、商业性）",
                priority=5,
                parallel_group="core",
                depends_on=[],
            ),
            AnalysisDimension(
                name="risk_assessment",
                description="需求的风险评估和可行性分析",
                priority=4,
                parallel_group="evaluation",
                depends_on=["professional_analysis"],
            ),
            AnalysisDimension(
                name="priority_dependency",
                description="需求的优先级和依赖关系分析",
                priority=3,
                parallel_group="evaluation",
                depends_on=["professional_analysis"],
            ),
            AnalysisDimension(
                name="clarification_questions",
                description="智能澄清问题生成",
                priority=5,
                parallel_group="core",
                depends_on=[],
            ),
            AnalysisDimension(
                name="implementation_strategy",
                description="实现策略和技术路线分析",
                priority=3,
                parallel_group="strategy",
                depends_on=["professional_analysis", "codebase_alignment"],
            ),
        ]

    async def analyze_requirement(
        self, content: str, project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行多维度需求分析"""
        start_time = time.time()
        logger.info(f"开始多维度需求分析，包含 {len(self.dimensions)} 个维度")

        try:
            # 按并行组组织分析任务
            parallel_groups = self._organize_parallel_groups()

            # 存储所有维度的结果
            dimension_results = {}

            # 按依赖关系分阶段执行
            for stage, groups in enumerate(parallel_groups, 1):
                logger.info(f"执行第 {stage} 阶段分析，包含 {len(groups)} 个并行组")

                # 并行执行当前阶段的所有组
                stage_tasks = []
                for group_name, dimensions in groups.items():
                    task = self._execute_parallel_group(
                        group_name,
                        dimensions,
                        content,
                        project_context,
                        dimension_results,
                    )
                    stage_tasks.append(task)

                # 等待当前阶段完成
                stage_results = await asyncio.gather(
                    *stage_tasks, return_exceptions=True
                )

                # 合并阶段结果
                for group_result in stage_results:
                    if isinstance(group_result, dict):
                        dimension_results.update(group_result)
                    elif isinstance(group_result, Exception):
                        logger.error(f"并行组执行失败: {group_result}")

            # 生成综合分析报告
            comprehensive_report = await self._generate_comprehensive_report(
                content, dimension_results, project_context
            )

            # 计算总体质量评分
            quality_score = self._calculate_quality_score(dimension_results)

            total_time = time.time() - start_time
            logger.info(
                f"多维度分析完成，总耗时: {total_time:.2f}秒，质量评分: {quality_score}/100"
            )

            return {
                "session_id": f"multi_dim_{int(time.time())}",
                "status": "completed",
                "analysis_method": "Multi_Dimensional_Parallel_Analysis",
                "processing_time": total_time,
                "quality_score": quality_score,
                "dimension_results": dimension_results,
                "comprehensive_report": comprehensive_report,
                "clarification_questions": self._extract_clarification_questions(
                    dimension_results
                ),
                "conflicts_detected": self._extract_conflicts(dimension_results),
                "recommendations": self._extract_recommendations(dimension_results),
                "confidence": min(0.95, quality_score / 100),
                "analysis_complete": True,
            }

        except Exception as e:
            logger.error(f"多维度分析失败: {e}")
            raise RuntimeError(f"多维度需求分析失败: {str(e)}")

    def _organize_parallel_groups(self) -> List[Dict[str, List[AnalysisDimension]]]:
        """按依赖关系组织并行组"""
        # 简化实现：按并行组名称分组，实际应该考虑依赖关系
        groups_by_stage = []

        # 第一阶段：无依赖的核心分析
        stage1 = {}
        for dim in self.dimensions:
            if not dim.depends_on:
                if dim.parallel_group not in stage1:
                    stage1[dim.parallel_group] = []
                stage1[dim.parallel_group].append(dim)

        if stage1:
            groups_by_stage.append(stage1)

        # 第二阶段：依赖第一阶段的分析
        stage2 = {}
        for dim in self.dimensions:
            if dim.depends_on and any(
                dep in [d.name for d in self.dimensions if not d.depends_on]
                for dep in dim.depends_on
            ):
                if dim.parallel_group not in stage2:
                    stage2[dim.parallel_group] = []
                stage2[dim.parallel_group].append(dim)

        if stage2:
            groups_by_stage.append(stage2)

        return groups_by_stage

    async def _execute_parallel_group(
        self,
        group_name: str,
        dimensions: List[AnalysisDimension],
        content: str,
        project_context: Optional[Dict],
        previous_results: Dict[str, DimensionResult],
    ) -> Dict[str, DimensionResult]:
        """执行并行组内的所有维度分析"""
        logger.info(f"执行并行组 '{group_name}'，包含 {len(dimensions)} 个维度")

        # 创建组内并行任务
        tasks = []
        for dimension in dimensions:
            task = self._analyze_single_dimension(
                dimension, content, project_context, previous_results
            )
            tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        group_results = {}
        for i, result in enumerate(results):
            dimension = dimensions[i]
            if isinstance(result, DimensionResult):
                group_results[dimension.name] = result
            else:
                # 创建失败结果
                group_results[dimension.name] = DimensionResult(
                    dimension_name=dimension.name,
                    status="failed",
                    result={"error": str(result)},
                    processing_time=0,
                    confidence=0,
                    warnings=[f"分析失败: {result}"],
                    conflicts=[],
                )

        logger.info(f"并行组 '{group_name}' 执行完成")
        return group_results

    async def _analyze_single_dimension(
        self,
        dimension: AnalysisDimension,
        content: str,
        project_context: Optional[Dict],
        previous_results: Dict[str, DimensionResult],
    ) -> DimensionResult:
        """执行单个维度的分析"""
        start_time = time.time()
        logger.info(f"开始分析维度: {dimension.name}")

        try:
            # 根据维度类型选择分析方法
            if dimension.name == "goal_alignment":
                result = await self._analyze_goal_alignment(content, project_context)
            elif dimension.name == "knowledge_alignment":
                result = await self._analyze_knowledge_alignment(content)
            elif dimension.name == "codebase_alignment":
                result = await self._analyze_codebase_alignment(content)
            elif dimension.name == "professional_analysis":
                result = await self._analyze_professional_aspects(content)
            elif dimension.name == "risk_assessment":
                result = await self._analyze_risks(content, previous_results)
            elif dimension.name == "priority_dependency":
                result = await self._analyze_priority_dependency(
                    content, previous_results
                )
            elif dimension.name == "clarification_questions":
                result = await self._generate_clarification_questions(content)
            elif dimension.name == "implementation_strategy":
                result = await self._analyze_implementation_strategy(
                    content, previous_results
                )
            else:
                raise ValueError(f"未知的分析维度: {dimension.name}")

            processing_time = time.time() - start_time
            logger.info(
                f"维度 {dimension.name} 分析完成，耗时: {processing_time:.2f}秒"
            )

            return DimensionResult(
                dimension_name=dimension.name,
                status="success",
                result=result,
                processing_time=processing_time,
                confidence=result.get("confidence", 0.8),
                warnings=result.get("warnings", []),
                conflicts=result.get("conflicts", []),
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"维度 {dimension.name} 分析失败: {e}")

            return DimensionResult(
                dimension_name=dimension.name,
                status="failed",
                result={"error": str(e)},
                processing_time=processing_time,
                confidence=0,
                warnings=[f"分析失败: {e}"],
                conflicts=[],
            )

    async def _analyze_goal_alignment(
        self, content: str, project_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """分析需求与整体目标的相关性和冲突性"""
        prompt = f"""作为项目目标分析专家，请分析以下用户需求与项目整体目标的相关性和潜在冲突：

用户需求："{content}"

项目上下文：{project_context or "无具体项目上下文"}

请从以下维度分析：
1. 目标相关性：需求与项目目标的匹配度（0-100%）
2. 战略一致性：需求是否符合整体战略方向
3. 冲突检测：是否与已有目标产生冲突
4. 优先级建议：基于目标一致性的优先级建议

返回JSON格式：
{{
    "goal_relevance_score": 85,
    "strategic_alignment": "high/medium/low",
    "conflicts": ["冲突描述1", "冲突描述2"],
    "alignment_analysis": "详细分析说明",
    "priority_recommendation": "high/medium/low",
    "confidence": 0.9
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response, "goal_alignment")

    async def _analyze_knowledge_alignment(self, content: str) -> Dict[str, Any]:
        """分析需求与知识库的相关性和冲突性"""
        # 搜索相关知识
        related_knowledge = await self.knowledge_base.search_relevant(content)

        prompt = f"""作为知识管理专家，请分析以下用户需求与已有知识库的相关性和冲突：

用户需求："{content}"

相关知识库内容：
{related_knowledge[:1000] if related_knowledge else "未找到相关知识"}

请分析：
1. 知识相关性：需求与已有知识的相关程度
2. 知识覆盖度：已有知识对需求的覆盖程度
3. 知识冲突：是否与已有知识产生冲突
4. 知识缺口：需要补充的知识点

返回JSON格式：
{{
    "knowledge_relevance_score": 75,
    "coverage_percentage": 60,
    "conflicts": ["冲突描述"],
    "knowledge_gaps": ["缺口1", "缺口2"],
    "related_topics": ["主题1", "主题2"],
    "confidence": 0.85
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response, "knowledge_alignment")

    async def _analyze_codebase_alignment(self, content: str) -> Dict[str, Any]:
        """分析需求与代码库的相关性和冲突性"""
        # 分析代码库
        codebase_analysis = await self.code_analyzer.analyze_requirement_impact(content)

        prompt = f"""作为代码架构专家，请分析以下用户需求与现有代码库的相关性和冲突：

用户需求："{content}"

代码库分析结果：
{codebase_analysis[:1000] if codebase_analysis else "无代码库分析结果"}

请分析：
1. 代码相关性：需求与现有代码的相关程度
2. 实现可行性：基于现有代码架构的实现难度
3. 架构冲突：是否与现有架构产生冲突
4. 重构需求：需要的代码重构工作

返回JSON格式：
{{
    "code_relevance_score": 70,
    "implementation_feasibility": "high/medium/low",
    "architecture_conflicts": ["冲突描述"],
    "refactoring_requirements": ["重构需求1", "重构需求2"],
    "affected_modules": ["模块1", "模块2"],
    "confidence": 0.8
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response, "codebase_alignment")

    async def _analyze_professional_aspects(self, content: str) -> Dict[str, Any]:
        """专业需求分析（功能性、技术性、商业性）"""
        prompt = f"""作为资深需求分析师，请对以下需求进行专业的多维度分析：

用户需求："{content}"

请从以下维度进行专业分析：
1. 功能性分析：核心功能、边界条件、性能要求
2. 技术性分析：技术复杂度、技术风险、技术选型
3. 商业性分析：商业价值、成本效益、市场影响
4. 可行性分析：技术可行性、资源可行性、时间可行性

返回JSON格式：
{{
    "functional_analysis": {{
        "core_functions": ["功能1", "功能2"],
        "boundary_conditions": ["条件1", "条件2"],
        "performance_requirements": ["性能要求1", "性能要求2"]
    }},
    "technical_analysis": {{
        "complexity_level": "high/medium/low",
        "technical_risks": ["风险1", "风险2"],
        "recommended_tech_stack": ["技术1", "技术2"]
    }},
    "business_analysis": {{
        "business_value": "high/medium/low",
        "cost_benefit_ratio": 4.2,
        "market_impact": "描述"
    }},
    "feasibility_analysis": {{
        "technical_feasibility": "high/medium/low",
        "resource_feasibility": "high/medium/low",
        "time_feasibility": "high/medium/low"
    }},
    "confidence": 0.9
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response, "professional_analysis")

    async def _analyze_risks(
        self, content: str, previous_results: Dict[str, DimensionResult]
    ) -> Dict[str, Any]:
        """风险评估和可行性分析"""
        # 提取前面分析的结果作为上下文
        context = self._extract_context_for_risk_analysis(previous_results)

        prompt = f"""作为风险管理专家，基于前面的分析结果，请对以下需求进行风险评估：

用户需求："{content}"

前置分析结果：
{context}

请分析：
1. 技术风险：技术实现的风险点
2. 业务风险：业务层面的风险
3. 时间风险：进度和时间相关风险
4. 资源风险：人力和资源风险
5. 风险缓解策略

返回JSON格式：
{{
    "technical_risks": [
        {{"risk": "风险描述", "probability": "high/medium/low", "impact": "high/medium/low", "mitigation": "缓解策略"}}
    ],
    "business_risks": [...],
    "timeline_risks": [...],
    "resource_risks": [...],
    "overall_risk_level": "high/medium/low",
    "confidence": 0.85
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response, "risk_assessment")

    async def _analyze_priority_dependency(
        self, content: str, previous_results: Dict[str, DimensionResult]
    ) -> Dict[str, Any]:
        """优先级和依赖关系分析"""
        context = self._extract_context_for_priority_analysis(previous_results)

        prompt = f"""作为项目管理专家，基于前面的分析结果，请分析以下需求的优先级和依赖关系：

用户需求："{content}"

前置分析结果：
{context}

请分析：
1. 优先级评估：基于业务价值、技术复杂度、风险等因素
2. 依赖关系：与其他需求/功能的依赖关系
3. 实施顺序：推荐的实施顺序和里程碑
4. 关键路径：识别关键路径和瓶颈

返回JSON格式：
{{
    "priority_score": 85,
    "priority_level": "high/medium/low",
    "dependencies": ["依赖项1", "依赖项2"],
    "implementation_order": ["阶段1", "阶段2", "阶段3"],
    "critical_path": ["关键任务1", "关键任务2"],
    "estimated_timeline": "8-12周",
    "confidence": 0.8
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response, "priority_dependency")

    async def _generate_clarification_questions(self, content: str) -> Dict[str, Any]:
        """生成智能澄清问题"""
        prompt = f"""作为需求澄清专家，请为以下需求生成高质量的澄清问题：

用户需求："{content}"

请生成3-5个最关键的澄清问题，每个问题应该：
1. 针对需求中的关键模糊点
2. 有助于明确具体实现方案
3. 涵盖不同的分析维度（功能、技术、业务）

返回JSON格式：
{{
    "clarification_questions": [
        {{
            "id": "q1",
            "question": "具体问题内容",
            "text": "具体问题内容",
            "category": "功能需求/技术需求/业务需求",
            "priority": "high/medium/low",
            "purpose": "澄清目的和重要性"
        }}
    ],
    "total_questions": 4,
    "confidence": 0.9
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response, "clarification_questions")

    async def _analyze_implementation_strategy(
        self, content: str, previous_results: Dict[str, DimensionResult]
    ) -> Dict[str, Any]:
        """实现策略和技术路线分析"""
        context = self._extract_context_for_implementation_analysis(previous_results)

        prompt = f"""作为技术架构师，基于前面的分析结果，请制定以下需求的实现策略：

用户需求："{content}"

前置分析结果：
{context}

请制定：
1. 技术方案：推荐的技术栈和架构模式
2. 实现策略：分阶段实现策略
3. 资源规划：所需的人力和技术资源
4. 质量保证：测试和质量控制策略

返回JSON格式：
{{
    "technical_solution": {{
        "architecture_pattern": "微服务/单体/分层",
        "tech_stack": ["前端技术", "后端技术", "数据库"],
        "integration_approach": "集成方式"
    }},
    "implementation_strategy": {{
        "phases": ["阶段1", "阶段2", "阶段3"],
        "milestones": ["里程碑1", "里程碑2"],
        "parallel_tracks": ["并行工作1", "并行工作2"]
    }},
    "resource_planning": {{
        "team_size": 5,
        "skill_requirements": ["技能1", "技能2"],
        "estimated_effort": "人月"
    }},
    "quality_assurance": {{
        "testing_strategy": "测试策略",
        "quality_gates": ["质量关卡1", "质量关卡2"]
    }},
    "confidence": 0.85
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response, "implementation_strategy")

    def _parse_json_response(
        self, response: str, dimension_name: str
    ) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            import json
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("无法提取JSON数据")

        except Exception as e:
            logger.error(f"解析 {dimension_name} 响应失败: {e}")
            return {
                "error": f"解析失败: {e}",
                "raw_response": response[:500],
                "confidence": 0,
            }

    def _extract_context_for_risk_analysis(
        self, previous_results: Dict[str, DimensionResult]
    ) -> str:
        """提取风险分析所需的上下文"""
        context_parts = []

        if "professional_analysis" in previous_results:
            result = previous_results["professional_analysis"].result
            context_parts.append(f"专业分析结果: {result}")

        return "\n".join(context_parts[:3])  # 限制长度

    def _extract_context_for_priority_analysis(
        self, previous_results: Dict[str, DimensionResult]
    ) -> str:
        """提取优先级分析所需的上下文"""
        context_parts = []

        for key in ["goal_alignment", "professional_analysis"]:
            if key in previous_results:
                result = previous_results[key].result
                context_parts.append(f"{key}: {result}")

        return "\n".join(context_parts[:3])  # 限制长度

    def _extract_context_for_implementation_analysis(
        self, previous_results: Dict[str, DimensionResult]
    ) -> str:
        """提取实现分析所需的上下文"""
        context_parts = []

        for key in ["professional_analysis", "codebase_alignment", "risk_assessment"]:
            if key in previous_results:
                result = previous_results[key].result
                context_parts.append(f"{key}: {result}")

        return "\n".join(context_parts[:3])  # 限制长度

    async def _generate_comprehensive_report(
        self,
        content: str,
        dimension_results: Dict[str, DimensionResult],
        project_context: Optional[Dict],
    ) -> str:
        """生成综合分析报告"""
        # 提取所有成功的分析结果
        successful_results = {
            name: result
            for name, result in dimension_results.items()
            if result.status == "success"
        }

        prompt = f"""作为需求分析总监，请基于多维度分析结果，生成一份综合的需求分析报告：

原始需求："{content}"

多维度分析结果：
{str(successful_results)[:2000]}  # 限制长度

请生成一份结构化的综合报告，包括：
1. 执行摘要
2. 需求分析总结
3. 关键发现和洞察
4. 风险和机会
5. 建议和下一步行动

报告应该专业、简洁、可执行。"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            stream=False,
        )

        return response

    def _calculate_quality_score(
        self, dimension_results: Dict[str, DimensionResult]
    ) -> float:
        """计算总体质量评分"""
        if not dimension_results:
            return 0

        total_score = 0
        total_weight = 0

        for dimension in self.dimensions:
            if dimension.name in dimension_results:
                result = dimension_results[dimension.name]
                if result.status == "success":
                    score = result.confidence * 100
                    weight = dimension.priority
                    total_score += score * weight
                    total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0

    def _extract_clarification_questions(
        self, dimension_results: Dict[str, DimensionResult]
    ) -> List[Dict]:
        """提取澄清问题"""
        if "clarification_questions" in dimension_results:
            result = dimension_results["clarification_questions"].result
            return result.get("clarification_questions", [])
        return []

    def _extract_conflicts(
        self, dimension_results: Dict[str, DimensionResult]
    ) -> List[str]:
        """提取检测到的冲突"""
        conflicts = []
        for result in dimension_results.values():
            conflicts.extend(result.conflicts)
        return conflicts

    def _extract_recommendations(
        self, dimension_results: Dict[str, DimensionResult]
    ) -> List[str]:
        """提取建议"""
        recommendations = []

        # 从各个维度提取关键建议
        for name, result in dimension_results.items():
            if result.status == "success" and "recommendations" in result.result:
                recommendations.extend(result.result["recommendations"])

        return recommendations[:10]  # 限制数量
