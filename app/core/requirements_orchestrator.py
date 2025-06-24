"""
需求分析协调器
智能协调知识库、代码库和需求分析助手的协作
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from loguru import logger

from ..assistants.requirements.agents.requirement_clarifier import (
    RequirementClarifierAgent,
)
from ..modules.codebase.manager import CodebaseManager
from ..modules.codebase.types import CodeSearchQuery
from ..modules.knowledge_base.enhanced_service import EnhancedKnowledgeService
from ..modules.knowledge_base.types import KnowledgeQuery
from ..schema import RequirementAnalysisRequest, RequirementAnalysisResponse


class RequirementsOrchestrator:
    """需求分析协调器"""

    def __init__(self):
        """初始化协调器"""
        self.knowledge_service = EnhancedKnowledgeService()
        self.codebase_manager = CodebaseManager()
        self.clarifier_agent = RequirementClarifierAgent()

        logger.info("需求分析协调器初始化完成")

    async def analyze_requirement_comprehensive(
        self, request: RequirementAnalysisRequest
    ) -> RequirementAnalysisResponse:
        """
        综合分析需求
        整合知识库、代码库和需求分析助手的能力

        Args:
            request: 需求分析请求

        Returns:
            RequirementAnalysisResponse: 综合分析结果
        """
        logger.info(f"开始综合需求分析: {request.content[:100]}...")

        try:
            # 阶段1: 智能检索相关知识和代码
            knowledge_context, code_context = await self._gather_context(request)

            # 阶段2: 智能需求澄清
            clarification_result = await self._intelligent_clarification(
                request, knowledge_context, code_context
            )

            # 阶段3: 技术可行性评估
            feasibility_assessment = await self._assess_technical_feasibility(
                request, code_context
            )

            # 阶段4: 智能建议生成
            recommendations = await self._generate_intelligent_recommendations(
                request, knowledge_context, code_context, feasibility_assessment
            )

            # 构建综合响应
            response = RequirementAnalysisResponse(
                original_content=request.content,
                clarified_requirements=clarification_result["clarified_requirements"],
                technical_feasibility=feasibility_assessment,
                recommendations=recommendations,
                knowledge_insights=knowledge_context["insights"],
                code_insights=code_context["insights"],
                confidence_score=self._calculate_confidence_score(
                    knowledge_context, code_context, feasibility_assessment
                ),
                analysis_metadata={
                    "knowledge_sources": knowledge_context["sources"],
                    "code_sources": code_context["sources"],
                    "analysis_time": datetime.now().isoformat(),
                    "orchestrator_version": "1.0",
                },
            )

            logger.success(f"综合需求分析完成，置信度: {response.confidence_score:.2f}")
            return response

        except Exception as e:
            logger.error(f"综合需求分析失败: {e}")
            raise

    async def _gather_context(
        self, request: RequirementAnalysisRequest
    ) -> Tuple[Dict, Dict]:
        """
        智能收集上下文信息

        Args:
            request: 需求分析请求

        Returns:
            Tuple[Dict, Dict]: (知识库上下文, 代码库上下文)
        """
        logger.info("收集相关知识和代码上下文")

        # 并行收集知识库和代码库信息
        knowledge_task = self._gather_knowledge_context(request)
        code_task = self._gather_code_context(request)

        knowledge_context, code_context = await asyncio.gather(
            knowledge_task, code_task
        )

        return knowledge_context, code_context

    async def _gather_knowledge_context(
        self, request: RequirementAnalysisRequest
    ) -> Dict:
        """收集知识库上下文"""
        try:
            # 构建正确的知识查询对象
            knowledge_query = KnowledgeQuery(
                query_text=request.content,
                domains=[request.domain] if request.domain else None,
                limit=5,
                min_confidence=0.5,
                context=request.context or {},
            )

            # 智能搜索相关知识
            search_response = await self.knowledge_service.search_knowledge(
                knowledge_query
            )

            # 获取相关模板和最佳实践
            templates = []
            if request.domain:
                try:
                    # 注意：这里需要根据实际API调整
                    # templates = self.knowledge_service.get_templates_by_domain(request.domain)
                    pass
                except Exception as e:
                    logger.warning(f"获取模板失败: {e}")

            insights = []
            sources = []

            # 处理搜索结果
            for result in search_response.results:
                insights.append(
                    {
                        "type": "knowledge",
                        "content": result.get("content", "")[:200] + "...",
                        "relevance": result.get("score", 0.0),
                        "source": result.get("knowledge_base_id", "unknown"),
                    }
                )
                if result.get("knowledge_base_id"):
                    sources.append(result["knowledge_base_id"])

            return {
                "insights": insights,
                "sources": list(set(sources)),
                "templates": templates,
                "search_results": search_response.results,
            }

        except Exception as e:
            logger.warning(f"知识库上下文收集失败: {e}")
            return {
                "insights": [],
                "sources": [],
                "templates": [],
                "search_results": [],
            }

    async def _gather_code_context(self, request: RequirementAnalysisRequest) -> Dict:
        """收集代码库上下文"""
        try:
            # 获取所有代码库
            codebases = self.codebase_manager.list_codebases()
            codebase_ids = [cb.id for cb in codebases]

            if not codebase_ids:
                return {
                    "insights": [],
                    "sources": [],
                    "components": [],
                    "tech_stacks": [],
                }

            # 智能搜索相关组件
            search_query = CodeSearchQuery(
                query_text=request.content, codebase_ids=codebase_ids, max_results=10
            )

            component_results = self.codebase_manager.search_components(search_query)

            # 获取技术栈信息
            tech_stack_distribution = (
                self.codebase_manager.get_tech_stack_distribution()
            )

            insights = []
            sources = []

            # 分析组件相关性
            for result in component_results:
                insights.append(
                    {
                        "type": "component",
                        "component_name": result.component.name,
                        "component_type": result.component.type.value,
                        "file_path": result.component.file_path,
                        "relevance": result.relevance_score,
                        "complexity": result.component.complexity.value,
                    }
                )
                sources.append(result.codebase_id)

            # 分析技术栈
            for tech_name, count in tech_stack_distribution.items():
                insights.append(
                    {
                        "type": "tech_stack",
                        "technology": tech_name,
                        "usage_count": count,
                        "recommendation": self._get_tech_recommendation(tech_name),
                    }
                )

            return {
                "insights": insights,
                "sources": list(set(sources)),
                "components": component_results,
                "tech_stacks": tech_stack_distribution,
            }

        except Exception as e:
            logger.warning(f"代码库上下文收集失败: {e}")
            return {
                "insights": [],
                "sources": [],
                "components": [],
                "tech_stacks": {},
            }

    async def _intelligent_clarification(
        self,
        request: RequirementAnalysisRequest,
        knowledge_context: Dict,
        code_context: Dict,
    ) -> Dict:
        """增强版智能需求澄清"""
        logger.info("执行智能需求澄清")

        try:
            # 向澄清器智能体提供需求和上下文
            clarifier_input = f"""
用户需求: {request.content}

相关知识上下文:
{self._format_context_for_clarifier(knowledge_context)}

相关代码上下文:
{self._format_context_for_clarifier(code_context)}

请基于上述上下文进行专业的需求澄清分析。
"""

            # 使用智能体的step方法进行澄清
            self.clarifier_agent.update_memory("user", clarifier_input)
            clarification_response = await self.clarifier_agent.step()

            return {
                "clarified_requirements": clarification_response,
                "clarity_score": getattr(self.clarifier_agent, "clarity_score", 0.7),
                "clarification_questions": getattr(
                    self.clarifier_agent, "clarification_questions", []
                ),
                "context_enhanced": True,
            }

        except Exception as e:
            logger.error(f"智能需求澄清失败: {e}")
            # 回退到基础澄清
            return {
                "clarified_requirements": request.content,
                "clarity_score": 0.5,
                "clarification_questions": [],
                "context_enhanced": False,
            }

    def _format_context_for_clarifier(self, context: Dict) -> str:
        """格式化上下文信息供澄清器使用"""
        insights = context.get("insights", [])
        if not insights:
            return "暂无相关上下文信息"

        formatted_insights = []
        for insight in insights[:3]:  # 只取前3个最相关的
            insight_type = insight.get("type", "unknown")
            content = insight.get("content", "")
            relevance = insight.get("relevance", 0.0)
            formatted_insights.append(
                f"- [{insight_type}] {content} (相关度: {relevance:.2f})"
            )

        return "\n".join(formatted_insights)

    async def _assess_technical_feasibility(
        self, request: RequirementAnalysisRequest, code_context: Dict
    ) -> Dict:
        """评估技术可行性"""
        logger.info("评估技术可行性")

        try:
            tech_stacks = code_context.get("tech_stacks", {})
            components = code_context.get("components", [])

            # 技术栈兼容性分析
            tech_compatibility = self._analyze_tech_compatibility(request, tech_stacks)

            # 组件复用性分析
            component_reusability = self._analyze_component_reusability(
                request, components
            )

            # 综合可行性评估
            feasibility_score = (tech_compatibility + component_reusability) / 2

            return {
                "feasible": feasibility_score >= 0.6,
                "feasibility_score": feasibility_score,
                "tech_compatibility": tech_compatibility,
                "component_reusability": component_reusability,
                "recommendations": self._generate_feasibility_recommendations(
                    feasibility_score, tech_stacks, components
                ),
                "risks": self._identify_technical_risks(request, code_context),
            }

        except Exception as e:
            logger.error(f"技术可行性评估失败: {e}")
            return {
                "feasible": True,  # 默认可行
                "feasibility_score": 0.7,
                "tech_compatibility": 0.7,
                "component_reusability": 0.7,
                "recommendations": ["建议进行详细的技术调研"],
                "risks": ["技术评估不完整，存在未知风险"],
            }

    def _generate_feasibility_recommendations(
        self, score: float, tech_stacks: Dict, components: List
    ) -> List[str]:
        """生成可行性建议"""
        recommendations = []

        if score < 0.4:
            recommendations.append("建议重新考虑技术方案，当前可行性较低")
        elif score < 0.7:
            recommendations.append("建议进行技术预研，验证关键技术点")
        else:
            recommendations.append("技术可行性良好，可以开始详细设计")

        if tech_stacks:
            most_used_tech = max(tech_stacks.items(), key=lambda x: x[1])
            recommendations.append(f"建议优先考虑 {most_used_tech[0]} 技术栈")

        if len(components) > 5:
            recommendations.append("发现多个可复用组件，建议制定组件复用策略")

        return recommendations

    def _identify_technical_risks(
        self, request: RequirementAnalysisRequest, code_context: Dict
    ) -> List[str]:
        """识别技术风险"""
        risks = []

        components = code_context.get("components", [])
        tech_stacks = code_context.get("tech_stacks", {})

        if not components:
            risks.append("缺乏相关组件，需要从零开发")

        if not tech_stacks:
            risks.append("技术栈信息不足，无法评估兼容性")

        # 基于需求内容的风险评估
        if "实时" in request.content or "real-time" in request.content.lower():
            risks.append("实时需求可能带来性能和架构挑战")

        if "大数据" in request.content or "big data" in request.content.lower():
            risks.append("大数据处理需要考虑存储和计算资源")

        return risks

    async def _generate_intelligent_recommendations(
        self,
        request: RequirementAnalysisRequest,
        knowledge_context: Dict,
        code_context: Dict,
        feasibility_assessment: Dict,
    ) -> List[str]:
        """生成智能建议"""
        logger.info("生成智能建议")

        recommendations = []

        # 基于知识库的建议
        knowledge_insights = knowledge_context.get("insights", [])
        if knowledge_insights:
            recommendations.append(
                f"基于知识库分析，发现 {len(knowledge_insights)} 个相关最佳实践，建议参考应用"
            )

        # 基于代码库的建议
        code_insights = code_context.get("insights", [])
        reusable_components = [c for c in code_insights if c.get("type") == "component"]
        if reusable_components:
            recommendations.append(
                f"发现 {len(reusable_components)} 个可复用组件，建议优先复用以提升开发效率"
            )

        # 基于可行性评估的建议
        if feasibility_assessment.get("feasible", True):
            recommendations.append(
                f"技术可行性良好（{feasibility_assessment.get('feasibility_score', 0.7):.2f}），建议按计划推进"
            )
        else:
            recommendations.append("技术可行性存在风险，建议进行技术预研和方案调整")

        return recommendations

    def _analyze_tech_compatibility(
        self, request: RequirementAnalysisRequest, tech_stacks: Dict
    ) -> float:
        """分析技术栈兼容性"""
        if not tech_stacks:
            return 0.5  # 中性评分

        # 简单的关键词匹配评估（实际项目中可以更复杂）
        requirement_lower = request.content.lower()

        # 计算技术栈相关性
        total_weight = sum(tech_stacks.values())
        if total_weight == 0:
            return 0.5

        compatibility_score = 0.0

        # 基于技术栈使用频率的简单评估
        for tech, count in tech_stacks.items():
            weight = count / total_weight

            # 简单的技术匹配逻辑
            if tech.lower() in requirement_lower:
                compatibility_score += weight * 1.0
            else:
                compatibility_score += weight * 0.6  # 基础兼容性

        return min(compatibility_score, 1.0)

    def _analyze_component_reusability(
        self, request: RequirementAnalysisRequest, components: List
    ) -> float:
        """分析组件复用性"""
        if not components:
            return 0.3  # 无组件可复用

        # 计算相关组件的比例
        total_components = len(components)
        high_relevance_components = sum(
            1 for comp in components if comp.relevance_score > 0.7
        )

        reusability_ratio = (
            high_relevance_components / total_components if total_components > 0 else 0
        )

        # 转换为0-1评分
        return min(reusability_ratio * 1.5, 1.0)  # 1.5倍权重

    def _calculate_confidence_score(
        self, knowledge_context: Dict, code_context: Dict, feasibility_assessment: Dict
    ) -> float:
        """计算综合置信度"""
        # 知识库覆盖度
        knowledge_coverage = min(len(knowledge_context.get("insights", [])) / 5, 1.0)

        # 代码库覆盖度
        code_coverage = min(len(code_context.get("insights", [])) / 10, 1.0)

        # 可行性评估
        feasibility_score = feasibility_assessment.get("feasibility_score", 0.5)

        # 加权平均
        confidence = (
            knowledge_coverage * 0.3 + code_coverage * 0.3 + feasibility_score * 0.4
        )

        return round(confidence, 2)

    def _get_tech_recommendation(self, tech_name: str) -> str:
        """获取技术推荐建议"""
        tech_recommendations = {
            "python": "成熟稳定，适合快速开发",
            "javascript": "前端主流，生态丰富",
            "java": "企业级应用的首选",
            "react": "现代化前端框架",
            "vue": "渐进式前端框架",
            "django": "全栈Web开发框架",
            "flask": "轻量级Web框架",
            "spring": "企业级Java框架",
        }

        return tech_recommendations.get(tech_name.lower(), "技术栈稳定可靠")

    async def get_collaboration_status(self) -> Dict:
        """获取协作状态"""
        try:
            # 检查各模块状态
            knowledge_status = await self._check_knowledge_service_status()
            codebase_status = await self._check_codebase_service_status()
            clarifier_status = self._check_clarifier_status()

            return {
                "orchestrator_status": "active",
                "knowledge_service": knowledge_status,
                "codebase_service": codebase_status,
                "clarifier_agent": clarifier_status,
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取协作状态失败: {e}")
            return {
                "orchestrator_status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def _check_knowledge_service_status(self) -> Dict:
        """检查知识库服务状态"""
        try:
            stats = self.knowledge_service.get_statistics()
            return {
                "status": "active",
                "knowledge_bases": stats.get("total_knowledge_bases", 0),
                "total_entries": stats.get("total_entries", 0),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _check_codebase_service_status(self) -> Dict:
        """检查代码库服务状态"""
        try:
            stats = self.codebase_manager.get_statistics()
            return {
                "status": "active",
                "codebases": stats.get("total_codebases", 0),
                "components": stats.get("total_components", 0),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_clarifier_status(self) -> Dict:
        """检查澄清器状态"""
        return {
            "status": "active",
            "agent_state": self.clarifier_agent.state.value,
            "current_step": self.clarifier_agent.current_step,
            "max_steps": self.clarifier_agent.max_steps,
        }
