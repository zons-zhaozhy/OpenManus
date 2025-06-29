"""
需求澄清工具类

提供需求澄清相关的核心功能，包括：
1. 需求分析
2. 澄清点识别
3. 澄清执行
4. 结果验证
"""

import hashlib
import time
from typing import Any, Dict, List, Optional

from app.core.cache import get_cache_manager
from app.core.performance_controller import get_performance_controller
from app.core.performance_metrics import get_performance_metrics
from app.llm import LLM
from app.logger import get_logger

logger = get_logger(__name__)


class RequirementClarification:
    """需求澄清工具类"""

    def __init__(self, llm: LLM):
        """初始化需求澄清工具"""
        self.llm = llm
        self.performance_controller = get_performance_controller()
        self.cache = get_cache_manager()
        self.metrics = get_performance_metrics()

    def _generate_cache_key(self, requirement: str) -> str:
        """生成缓存键"""
        return f"quick_analysis_{hashlib.md5(requirement.encode()).hexdigest()}"

    @get_performance_controller().timeout_control(timeout=30)
    async def quick_analyze(self, requirement: str) -> Dict[str, Any]:
        """
        快速分析需求 - 30秒超时

        Args:
            requirement: 原始需求

        Returns:
            Dict[str, Any]: 快速分析结果
        """
        start_time = time.time()
        success = False

        try:
            # 检查缓存
            cache_key = self._generate_cache_key(requirement)
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.info("使用缓存的快速分析结果")
                duration = time.time() - start_time
                await self.metrics.record_quick_analysis(duration, True)
                return cached_result

            prompt = f"""请快速分析以下需求，重点关注：
1. 核心需求点（最多3个）
2. 主要风险（最多2个）
3. 关键建议（最多2个）

需求内容：
{requirement}

请提供简明扼要的分析。"""

            response = await self.llm.ask(
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                max_tokens=300,  # 限制输出长度
            )

            # 解析响应
            lines = response.split("\n")
            result = {
                "core_points": [],
                "risks": [],
                "suggestions": [],
                "confidence": 0.8,
            }

            current_section = None
            for line in lines:
                line = line.strip()
                if "核心需求" in line:
                    current_section = "core_points"
                elif "主要风险" in line:
                    current_section = "risks"
                elif "关键建议" in line:
                    current_section = "suggestions"
                elif line.startswith("- ") and current_section:
                    result[current_section].append(line[2:])

            # 缓存结果
            await self.cache.set(cache_key, result, expire=3600)  # 1小时过期

            success = True
            return result

        except Exception as e:
            logger.error(f"快速需求分析失败: {e}")
            raise
        finally:
            duration = time.time() - start_time
            await self.metrics.record_quick_analysis(duration, success)

    async def analyze_requirement(
        self, requirement: str, mode: str = "standard"
    ) -> Dict[str, Any]:
        """
        分析需求内容

        Args:
            requirement: 原始需求
            mode: 分析模式 ("quick", "standard", "deep")

        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            if mode == "quick":
                return await self.quick_analyze(requirement)

            prompt = f"""请分析以下需求：

{requirement}

分析要点：
1. 需求的完整性
2. 需求的清晰度
3. 需求的一致性
4. 需求的可行性
5. 潜在的风险点

请提供详细分析。"""

            response = await self.llm.ask(
                messages=[{"role": "system", "content": prompt}], temperature=0.3
            )

            return {
                "analysis": response,
                "timestamp": "2025-06-28T18:00:00Z",
                "confidence": 0.85,
            }

        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            raise

    async def identify_clarification_points(
        self, analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        识别需要澄清的点

        Args:
            analysis_result: 需求分析结果

        Returns:
            List[Dict[str, Any]]: 澄清点列表
        """
        try:
            prompt = f"""基于以下分析结果，识别需要澄清的关键点：

{analysis_result.get('analysis', '')}

请列出：
1. 模糊不清的点
2. 缺失的信息
3. 需要确认的假设
4. 潜在的冲突点

请提供结构化的清单。"""

            response = await self.llm.ask(
                messages=[{"role": "system", "content": prompt}], temperature=0.3
            )

            # 解析响应为结构化数据
            points = []
            current_point = {}
            for line in response.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    if current_point:
                        points.append(current_point)
                    current_point = {"point": line[2:], "type": "unclear"}
                elif line.startswith("  "):
                    if "details" not in current_point:
                        current_point["details"] = []
                    current_point["details"].append(line.strip())

            if current_point:
                points.append(current_point)

            return points

        except Exception as e:
            logger.error(f"澄清点识别失败: {e}")
            raise

    async def execute_clarification(
        self,
        requirement: str,
        clarification_points: List[Dict[str, Any]],
        context: Optional[Dict] = None,
    ) -> str:
        """
        执行澄清

        Args:
            requirement: 原始需求
            clarification_points: 澄清点列表
            context: 上下文信息

        Returns:
            str: 澄清后的需求
        """
        try:
            # 构建提示词
            points_text = "\n".join(
                f"- {point['point']}\n  " + "\n  ".join(point.get("details", []))
                for point in clarification_points
            )

            context_text = ""
            if context:
                if context.get("knowledge"):
                    context_text += f"\n相关知识：\n{context['knowledge']}"
                if context.get("code_analysis"):
                    context_text += f"\n代码分析：\n{context['code_analysis']}"

            prompt = f"""请基于以下信息对需求进行澄清：

原始需求：
{requirement}

需要澄清的点：
{points_text}

{context_text}

请提供：
1. 针对每个澄清点的具体问题
2. 可能的答案选项
3. 澄清建议

注意保持专业性和完整性。"""

            response = await self.llm.ask(
                messages=[{"role": "system", "content": prompt}], temperature=0.4
            )

            return response

        except Exception as e:
            logger.error(f"需求澄清执行失败: {e}")
            raise

    async def validate_clarification(self, clarified_requirement: str) -> str:
        """
        验证澄清结果

        Args:
            clarified_requirement: 澄清后的需求

        Returns:
            str: 验证后的需求
        """
        try:
            prompt = f"""请验证以下澄清后的需求：

{clarified_requirement}

验证要点：
1. 是否解决了所有模糊点
2. 是否保持了一致性
3. 是否引入了新的问题
4. 是否符合业务目标
5. 是否技术可行

请提供验证结果和改进建议。"""

            response = await self.llm.ask(
                messages=[{"role": "system", "content": prompt}], temperature=0.3
            )

            return response

        except Exception as e:
            logger.error(f"澄清结果验证失败: {e}")
            raise
