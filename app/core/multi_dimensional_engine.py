"""
多维度并行分析引擎
实现用户建议的多维度需求分析

分析维度：
1. 需求与整体目标的相关性和冲突性分析
2. 需求与知识库的相关性和冲突性分析
3. 需求与代码库的相关性和冲突性分析
4. 需求的专业分析（功能性、技术性、商业性）
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import Config
from app.llm import LLM
from app.logger import logger


@dataclass
class AnalysisDimension:
    """分析维度定义"""

    name: str
    description: str
    priority: int  # 1-5优先级
    parallel_group: str  # 并行组标识


@dataclass
class DimensionResult:
    """维度分析结果"""

    dimension_name: str
    status: str  # success, failed, skipped
    result: Dict[str, Any]
    processing_time: float
    confidence: float
    conflicts: List[str]


class MultiDimensionalAnalysisEngine:
    """多维度并行分析引擎"""

    def __init__(self):
        self.config = Config()
        LLM.clear_instances()  # 清除旧实例
        self.llm = LLM()

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
            ),
            AnalysisDimension(
                name="knowledge_alignment",
                description="需求与知识库的相关性和冲突性分析",
                priority=4,
                parallel_group="alignment",
            ),
            AnalysisDimension(
                name="codebase_alignment",
                description="需求与代码库的相关性和冲突性分析",
                priority=4,
                parallel_group="alignment",
            ),
            AnalysisDimension(
                name="professional_analysis",
                description="需求的专业分析（功能性、技术性、商业性）",
                priority=5,
                parallel_group="core",
            ),
            AnalysisDimension(
                name="clarification_questions",
                description="智能澄清问题生成",
                priority=5,
                parallel_group="core",
            ),
            AnalysisDimension(
                name="risk_assessment",
                description="需求的风险评估和可行性分析",
                priority=4,
                parallel_group="evaluation",
            ),
        ]

    async def analyze_requirement(
        self, content: str, project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行多维度需求分析 - 优化版"""
        start_time = time.time()
        logger.info(f"开始多维度需求分析，包含 {len(self.dimensions)} 个维度")

        try:
            # 优化：所有维度真正并行执行，不分组
            logger.info("启用全并行模式，所有维度同时执行")

            # 创建全并行任务
            tasks = []
            for dimension in self.dimensions:
                task = self._analyze_dimension(dimension, content, project_context)
                tasks.append(task)

            # 全并行执行
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 整理结果
            all_results = {}
            for i, result in enumerate(results):
                dimension = self.dimensions[i]
                if isinstance(result, DimensionResult):
                    all_results[dimension.name] = result
                else:
                    # 创建失败结果
                    all_results[dimension.name] = DimensionResult(
                        dimension_name=dimension.name,
                        status="failed",
                        result={"error": str(result)},
                        processing_time=0,
                        confidence=0,
                        conflicts=[],
                    )

            # 生成综合报告
            comprehensive_report = await self._generate_report(content, all_results)

            # 计算质量评分
            quality_score = self._calculate_quality_score(all_results)

            total_time = time.time() - start_time
            logger.info(
                f"多维度分析完成，总耗时: {total_time:.2f}秒，质量评分: {quality_score}/100"
            )

            return {
                "session_id": f"multi_dim_{int(time.time())}",
                "status": "completed",
                "analysis_method": "Multi_Dimensional_Full_Parallel_Analysis",
                "processing_time": total_time,
                "quality_score": quality_score,
                "dimension_results": all_results,
                "comprehensive_report": comprehensive_report,
                "clarification_questions": self._extract_questions(all_results),
                "conflicts_detected": self._extract_conflicts(all_results),
                "performance_metrics": {
                    "dimensions_analyzed": len(self.dimensions),
                    "successful_dimensions": len(
                        [r for r in all_results.values() if r.status == "success"]
                    ),
                    "average_dimension_time": sum(
                        r.processing_time for r in all_results.values()
                    )
                    / len(all_results),
                    "parallelization_efficiency": (
                        len(self.dimensions)
                        * max(r.processing_time for r in all_results.values())
                        / total_time
                        if total_time > 0
                        else 0
                    ),
                },
                "confidence": min(0.95, quality_score / 100),
                "analysis_complete": True,
            }

        except Exception as e:
            logger.error(f"多维度分析失败: {e}")
            raise RuntimeError(f"多维度需求分析失败: {str(e)}")

    async def _analyze_dimension(
        self,
        dimension: AnalysisDimension,
        content: str,
        project_context: Optional[Dict],
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
            elif dimension.name == "clarification_questions":
                result = await self._generate_clarification_questions(content)
            elif dimension.name == "risk_assessment":
                result = await self._analyze_risks(content)
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
    "strategic_alignment": "high",
    "conflicts": ["冲突描述1", "冲突描述2"],
    "alignment_analysis": "详细分析说明",
    "priority_recommendation": "high",
    "confidence": 0.9
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response)

    async def _analyze_knowledge_alignment(self, content: str) -> Dict[str, Any]:
        """分析需求与知识库的相关性和冲突性"""
        prompt = f"""作为知识管理专家，请分析以下用户需求与已有知识库的相关性和冲突：

用户需求："{content}"

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

        return self._parse_json_response(response)

    async def _analyze_codebase_alignment(self, content: str) -> Dict[str, Any]:
        """分析需求与代码库的相关性和冲突性"""
        prompt = f"""作为代码架构专家，请分析以下用户需求与现有代码库的相关性和冲突：

用户需求："{content}"

请分析：
1. 代码相关性：需求与现有代码的相关程度
2. 实现可行性：基于现有代码架构的实现难度
3. 架构冲突：是否与现有架构产生冲突
4. 重构需求：需要的代码重构工作

返回JSON格式：
{{
    "code_relevance_score": 70,
    "implementation_feasibility": "high",
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

        return self._parse_json_response(response)

    async def _analyze_professional_aspects(self, content: str) -> Dict[str, Any]:
        """专业需求分析（功能性、技术性、商业性）"""
        prompt = f"""作为资深需求分析师，请对以下需求进行专业的多维度分析：

用户需求："{content}"

请从以下维度进行专业分析：
1. 功能性分析：核心功能、边界条件、性能要求
2. 技术性分析：技术复杂度、技术风险、技术选型
3. 商业性分析：商业价值、成本效益、市场影响

返回JSON格式：
{{
    "functional_analysis": {{
        "core_functions": ["功能1", "功能2"],
        "boundary_conditions": ["条件1", "条件2"],
        "performance_requirements": ["性能要求1", "性能要求2"]
    }},
    "technical_analysis": {{
        "complexity_level": "medium",
        "technical_risks": ["风险1", "风险2"],
        "recommended_tech_stack": ["技术1", "技术2"]
    }},
    "business_analysis": {{
        "business_value": "high",
        "cost_benefit_ratio": 4.2,
        "market_impact": "正面影响描述"
    }},
    "confidence": 0.9
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response)

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
            "category": "功能需求",
            "priority": "high",
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

        return self._parse_json_response(response)

    async def _analyze_risks(self, content: str) -> Dict[str, Any]:
        """风险评估和可行性分析"""
        prompt = f"""作为风险管理专家，请对以下需求进行风险评估：

用户需求："{content}"

请分析：
1. 技术风险：技术实现的风险点
2. 业务风险：业务层面的风险
3. 时间风险：进度和时间相关风险
4. 资源风险：人力和资源风险

返回JSON格式：
{{
    "technical_risks": [
        {{"risk": "风险描述", "probability": "medium", "impact": "high", "mitigation": "缓解策略"}}
    ],
    "business_risks": [...],
    "timeline_risks": [...],
    "resource_risks": [...],
    "overall_risk_level": "medium",
    "confidence": 0.85
}}"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
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
            logger.error(f"解析响应失败: {e}")
            return {
                "error": f"解析失败: {e}",
                "raw_response": response[:500],
                "confidence": 0,
            }

    async def _generate_report(
        self, content: str, dimension_results: Dict[str, DimensionResult]
    ) -> str:
        """生成综合分析报告"""
        successful_results = {
            name: result
            for name, result in dimension_results.items()
            if result.status == "success"
        }

        prompt = f"""基于多维度分析结果，生成需求分析综合报告：

原始需求："{content}"

分析结果概要：
{str({k: v.result for k, v in successful_results.items()})[:1500]}

请生成简洁的综合报告，包括：
1. 需求分析总结
2. 关键发现
3. 主要风险和冲突
4. 建议和下一步"""

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

    def _extract_questions(
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
