"""
LLM驱动的需求分析引擎
"""

import time
from typing import Any, Dict

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config_manager import ConfigManager
from app.llm import LLM


class LLMAnalysisEngine:
    """LLM驱动的需求分析引擎"""

    def __init__(self):
        self.config = ConfigManager()
        # 清除LLM单例实例，确保使用最新配置
        LLM.clear_instances()
        self.llm = LLM()

    async def analyze_requirement(self, content: str) -> Dict[str, Any]:
        """
        使用LLM分析用户需求 - 并行优化版本

        Args:
            content: 用户输入的需求内容

        Returns:
            分析结果字典

        Raises:
            Exception: LLM分析失败时抛出异常
        """
        start_time = time.time()

        # 检查是否启用LLM分析
        if not self.config.get("requirements_analysis.enable_llm_analysis", True):
            raise RuntimeError("LLM分析已被禁用，无法进行需求分析")

        # 使用并行LLM分析提升性能
        try:
            logger.info("启动并行LLM分析以提升响应速度...")

            # 创建两个并行任务：基础分析 + 澄清问题生成
            import asyncio

            tasks = [
                self._quick_analysis_task(content),
                self._detailed_questions_task(content),
            ]

            # 并行执行，取最快完成的结果
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            quick_result, detailed_result = results

            # 如果两个都成功，合并结果；否则使用成功的那个
            if not isinstance(quick_result, Exception) and not isinstance(
                detailed_result, Exception
            ):
                # 合并两个结果
                merged_result = self._merge_parallel_results(
                    quick_result, detailed_result
                )
                logger.info("并行分析完成，结果已合并")
                return merged_result
            elif not isinstance(quick_result, Exception):
                logger.info("使用快速分析结果")
                return quick_result
            elif not isinstance(detailed_result, Exception):
                logger.info("使用详细分析结果")
                return detailed_result
            else:
                # 两个都失败，回退到串行模式
                logger.warning("并行分析失败，回退到串行模式")
                result = await self._llm_analysis_with_retry(content)
                if not result or not result.get("analysis_result"):
                    raise RuntimeError("LLM分析返回空结果")
                return result

        except Exception as e:
            logger.error(f"LLM需求分析失败: {e}")
            raise RuntimeError(f"需求分析失败: {str(e)}")

    async def _quick_analysis_task(self, content: str) -> Dict[str, Any]:
        """快速分析任务 - 专注于需求分类和基础信息"""
        prompt = f"""作为需求分析师，请快速分析以下需求的基础信息：

"{content}"

请返回JSON格式：
{{
    "requirement_type": "需求类型",
    "business_domain": "业务领域",
    "complexity": {{"level": "复杂度", "estimated_weeks": "预估周期"}},
    "summary": "简要分析"
}}
"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_quick_response(response, content, "quick")

    async def _detailed_questions_task(self, content: str) -> Dict[str, Any]:
        """详细问题生成任务 - 专注于澄清问题"""
        prompt = f"""作为需求分析师，请为以下需求生成专业的澄清问题：

"{content}"

请返回JSON格式：
{{
    "clarification_questions": [
        {{
            "id": "q1",
            "question": "具体问题",
            "purpose": "澄清目的"
        }}
    ]
}}
"""

        response = await self.llm.ask(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )

        return self._parse_quick_response(response, content, "questions")

    def _merge_parallel_results(
        self, quick_result: Dict, detailed_result: Dict
    ) -> Dict[str, Any]:
        """合并并行分析结果"""
        # 以快速分析为基础，补充详细问题
        merged = quick_result.copy()

        # 合并澄清问题
        quick_questions = quick_result.get("clarification_questions", [])
        detailed_questions = detailed_result.get("clarification_questions", [])

        # 去重并合并
        all_questions = quick_questions + detailed_questions
        unique_questions = []
        seen_questions = set()

        for q in all_questions:
            q_text = q.get("question", "")
            if q_text not in seen_questions:
                unique_questions.append(q)
                seen_questions.add(q_text)

        merged["clarification_questions"] = unique_questions[:4]  # 最多4个问题
        merged["analysis_method"] = "LLM_Parallel_Analysis"

        logger.info(f"合并结果：{len(unique_questions)} 个澄清问题")
        return merged

    def _parse_quick_response(
        self, response: str, content: str, task_type: str
    ) -> Dict[str, Any]:
        """解析快速分析响应"""
        try:
            import json
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                raise ValueError("无法提取JSON数据")

            return {
                "session_id": f"llm_{task_type}_{int(time.time())}",
                "status": "completed",
                "analysis_result": response,
                "structured_data": analysis_data,
                "clarification_questions": analysis_data.get(
                    "clarification_questions", []
                ),
                "analysis_method": f"LLM_{task_type.title()}_Analysis",
                "confidence_score": 0.85,
                "processing_time": time.time(),
                "confidence": 0.85,
                "progress": {
                    "current_stage": "快速分析完成",
                    "clarification_complete": False,
                    "analysis_complete": True,
                },
            }

        except Exception as e:
            logger.error(f"{task_type}分析解析失败: {e}")
            raise e

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _llm_analysis_with_retry(self, content: str) -> Dict[str, Any]:
        """
        带重试机制的LLM分析

        Args:
            content: 需求内容

        Returns:
            分析结果

        Raises:
            Exception: 重试后仍然失败
        """
        try:
            logger.info("开始LLM深度分析...")

            # 构建智能分析提示词
            prompt = self._build_analysis_prompt(content)

            # 记录请求详情
            logger.info(f"=== LLM请求开始 ===")
            logger.info(f"用户需求: {content}")
            logger.info(f"提示词长度: {len(prompt)} 字符")
            logger.info(
                f"温度参数: {self.config.get('requirements_analysis.temperature', 0.1)}"
            )
            logger.info(f"请求模型: {self.llm.model}")
            logger.info(f"最大tokens: {self.llm.max_tokens}")

            # 调用LLM
            start_time = time.time()
            response = await self.llm.ask(
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get("requirements_analysis.temperature", 0.1),
                stream=False,
            )
            request_duration = time.time() - start_time

            # 记录响应详情
            logger.info(f"=== LLM响应完成 ===")
            logger.info(f"响应时长: {request_duration:.2f} 秒")
            logger.info(f"响应长度: {len(response) if response else 0} 字符")
            logger.info(f"响应内容预览: {response[:200] if response else 'None'}...")

            # 解析响应
            result = self._parse_llm_response(response, content)

            # 记录解析结果
            questions_count = len(
                result.get("result", {}).get("clarification_questions", [])
            )
            logger.info(f"=== 分析结果统计 ===")
            logger.info(f"生成澄清问题数: {questions_count}")
            logger.info(
                f"分析方法: {result.get('result', {}).get('analysis_method', 'Unknown')}"
            )
            logger.info(f"置信度: {result.get('confidence', 'Unknown')}")
            logger.info(f"总处理时长: {request_duration:.2f} 秒")

            logger.info("LLM分析完成")
            return result

        except Exception as e:
            logger.error(f"=== LLM请求失败 ===")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误信息: {str(e)}")
            logger.warning(f"LLM请求失败: {e}")
            raise e

    def _build_analysis_prompt(self, content: str) -> str:
        """构建LLM分析提示词"""

        return f"""作为专业的软件需求分析师，请对以下用户需求进行深度智能分析：

"{content}"

请运用你的专业知识和经验，从以下维度进行全面分析：

1. **需求理解与分类**：
   - 识别需求类型（功能性/非功能性）
   - 判断应用领域和业务场景
   - 提取核心功能模块

2. **技术架构建议**：
   - 推荐适合的技术栈
   - 架构模式建议
   - 数据库设计思路

3. **关键澄清问题**：
   - 提出3-5个最关键的澄清问题
   - 每个问题都应该针对需求中的模糊点
   - 问题要专业且具体

4. **实现复杂度评估**：
   - 开发难度评级（简单/中等/复杂）
   - 预估开发周期
   - 主要技术挑战

5. **风险与建议**：
   - 潜在风险点
   - 实施建议
   - 优先级排序

请以JSON格式返回分析结果，结构如下：
{{
    "requirement_type": "需求类型",
    "business_domain": "业务领域",
    "core_functions": ["核心功能1", "核心功能2"],
    "tech_stack": {{
        "frontend": "前端技术",
        "backend": "后端技术",
        "database": "数据库"
    }},
    "architecture_pattern": "架构模式",
    "clarification_questions": [
        {{
            "id": "q1",
            "question": "具体问题1",
            "text": "具体问题1",
            "category": "功能需求",
            "priority": "high",
            "purpose": "澄清目的"
        }}
    ],
    "complexity": {{
        "level": "复杂度级别",
        "estimated_weeks": "预估周期",
        "main_challenges": ["挑战1", "挑战2"]
    }},
    "risks_and_suggestions": {{
        "risks": ["风险1", "风险2"],
        "suggestions": ["建议1", "建议2"],
        "priorities": ["优先级1", "优先级2"]
    }},
    "summary": "需求分析总结"
}}

请确保分析专业、准确、有深度，避免泛泛而谈。每个澄清问题必须包含question、text、category、priority字段。"""

    def _parse_llm_response(
        self, response: str, original_content: str
    ) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            import json
            import re

            logger.info(f"=== 开始解析LLM响应 ===")
            logger.info(f"原始响应长度: {len(response)} 字符")

            # 尝试提取JSON部分
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                logger.info(f"提取JSON字符串长度: {len(json_str)} 字符")
                logger.info(f"JSON字符串预览: {json_str[:300]}...")

                analysis_data = json.loads(json_str)
                logger.info(f"JSON解析成功")

                # 记录解析出的关键字段
                req_type = analysis_data.get("requirement_type", "Unknown")
                domain = analysis_data.get("business_domain", "Unknown")
                questions = analysis_data.get("clarification_questions", [])
                complexity = analysis_data.get("complexity", {})

                logger.info(f"需求类型: {req_type}")
                logger.info(f"业务领域: {domain}")
                logger.info(f"澄清问题数量: {len(questions)}")
                logger.info(f"复杂度等级: {complexity.get('level', 'Unknown')}")

            else:
                logger.error("无法从响应中找到JSON格式数据")
                logger.error(f"响应内容: {response[:500]}...")
                raise ValueError("无法从响应中提取JSON格式数据")

            # 直接返回扁平化的结构，避免嵌套
            return {
                "session_id": f"llm_deep_{int(time.time())}",
                "status": "completed",
                "analysis_result": response,
                "structured_data": analysis_data,
                "clarification_questions": analysis_data.get(
                    "clarification_questions", []
                ),
                "analysis_method": "LLM_Deep_Analysis",
                "confidence_score": 0.95,
                "processing_time": time.time(),
                "confidence": 0.95,
                "progress": {
                    "current_stage": "深度分析完成",
                    "clarification_complete": False,
                    "analysis_complete": True,
                },
            }

        except json.JSONDecodeError as e:
            logger.error(f"=== JSON解析失败 ===")
            logger.error(f"JSON错误: {str(e)}")
            logger.error(f"错误位置: 第{e.lineno}行，第{e.colno}列")
            logger.error(
                f"问题内容: {e.doc[max(0, e.pos-50):e.pos+50] if hasattr(e, 'doc') and e.doc else 'N/A'}"
            )
            raise ValueError(f"LLM响应格式错误: {e}")
        except Exception as e:
            logger.error(f"=== 响应解析异常 ===")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常信息: {str(e)}")
            raise ValueError(f"响应解析失败: {e}")


# 不再使用全局实例，每次都创建新实例以确保配置更新
