"""
Reflection Engine - 反思引擎
实现自我反思和评估机制，提升智能体的输出质量

参考：
- 自我反思和评估机制
- 质量评估框架
- 迭代改进方法
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from app.llm import LLM
from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReflectionResult:
    """反思结果数据结构"""

    quality_score: float
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReflectionEngine:
    """
    反思引擎 - 实现自我反思和评估机制

    功能：
    1. 评估输出质量
    2. 识别优势和不足
    3. 提供改进建议
    4. 支持迭代优化
    """

    def __init__(self, llm: Optional[LLM] = None):
        """初始化反思引擎"""
        self.llm = llm or LLM(config_name="reflection_engine")

    async def comprehensive_reflection(
        self,
        original_input: str,
        generated_output: str,
        task_description: str,
        evaluation_criteria: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        全面反思评估

        Args:
            original_input: 原始输入
            generated_output: 生成的输出
            task_description: 任务描述
            evaluation_criteria: 评估标准列表
            context: 上下文信息

        Returns:
            Dict[str, Any]: 反思结果
        """
        logger.info(f"🔍 开始全面反思评估: {task_description}")

        # 默认评估标准
        if evaluation_criteria is None:
            evaluation_criteria = [
                "准确性",
                "完整性",
                "清晰度",
                "相关性",
                "一致性",
                "创新性",
            ]

        # 构建反思提示词
        reflection_prompt = self._create_reflection_prompt(
            original_input, generated_output, task_description, evaluation_criteria, context
        )

        # 执行反思
        reflection_response = await self.llm.ask([{"role": "user", "content": reflection_prompt}])

        # 解析反思结果
        reflection_result = self._parse_reflection_response(reflection_response)

        logger.info(f"✓ 反思评估完成，质量评分: {reflection_result.get('quality_score', 0):.2f}")
        return reflection_result

    def _create_reflection_prompt(
        self,
        original_input: str,
        generated_output: str,
        task_description: str,
        evaluation_criteria: List[str],
        context: Optional[Dict],
    ) -> str:
        """创建反思提示词"""
        criteria_text = "\n".join([f"- {criterion}" for criterion in evaluation_criteria])
        context_text = ""
        if context:
            context_text = f"\n\n上下文信息:\n{context}"

        prompt = f"""作为一个专业的质量评估专家，请对以下内容进行全面的反思评估：

## 任务描述
{task_description}

## 原始输入
{original_input}

## 生成的输出
{generated_output}{context_text}

## 评估标准
{criteria_text}

请按照以下结构进行评估：

1. 质量评分（0-10分）：对整体质量的量化评估
2. 优势：列出3-5个主要优势
3. 不足：列出3-5个需要改进的方面
4. 洞察：提供2-3个关于输出内容的深度洞察
5. 改进建议：提供3-5个具体的改进建议

请确保评估全面、客观、具体，并提供可操作的改进建议。
"""
        return prompt

    def _parse_reflection_response(self, response: str) -> Dict[str, Any]:
        """解析反思响应"""
        result = {
            "quality_score": 0.0,
            "strengths": [],
            "weaknesses": [],
            "insights": [],
            "improvement_suggestions": [],
        }

        # 提取质量评分
        score_match = re.search(r"质量评分[：:]\s*(\d+(\.\d+)?)", response)
        if score_match:
            try:
                result["quality_score"] = float(score_match.group(1))
            except ValueError:
                result["quality_score"] = 5.0  # 默认中等分数

        # 提取优势
        strengths_section = self._extract_section(response, r"优势[：:]", r"不足[：:]")
        if strengths_section:
            result["strengths"] = self._extract_list_items(strengths_section)

        # 提取不足
        weaknesses_section = self._extract_section(response, r"不足[：:]", r"洞察[：:]")
        if weaknesses_section:
            result["weaknesses"] = self._extract_list_items(weaknesses_section)

        # 提取洞察
        insights_section = self._extract_section(response, r"洞察[：:]", r"改进建议[：:]")
        if insights_section:
            result["insights"] = self._extract_list_items(insights_section)

        # 提取改进建议
        suggestions_section = self._extract_section(response, r"改进建议[：:]", r"$")
        if suggestions_section:
            result["improvement_suggestions"] = self._extract_list_items(suggestions_section)

        return result

    def _extract_section(self, text: str, start_pattern: str, end_pattern: str) -> str:
        """提取文本中的特定部分"""
        pattern = f"{start_pattern}(.*?){end_pattern}"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_list_items(self, text: str) -> List[str]:
        """从文本中提取列表项"""
        items = []
        # 匹配数字或点号开头的列表项
        pattern = r"(?:^|\n)(?:\d+\.\s*|\-\s*|\*\s*)(.+?)(?=\n(?:\d+\.\s*|\-\s*|\*\s*)|$)"
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            item = match.group(1).strip()
            if item:
                items.append(item)
                
        # 如果没有找到列表项，尝试按行分割
        if not items and text:
            items = [line.strip() for line in text.split("\n") if line.strip()]
            
        return items

    async def quick_reflection(
        self, output: str, task_type: str
    ) -> Dict[str, Union[float, str]]:
        """
        快速反思评估

        Args:
            output: 需要评估的输出
            task_type: 任务类型

        Returns:
            Dict[str, Union[float, str]]: 快速评估结果
        """
        prompt = f"""请对以下{task_type}任务的输出进行快速质量评估：

输出内容：
{output}

请给出：
1. 质量评分（1-10分）
2. 一句话评价
"""

        response = await self.llm.ask([{"role": "user", "content": prompt}])
        
        # 提取评分和评价
        score_match = re.search(r"(\d+(\.\d+)?)", response)
        score = float(score_match.group(1)) if score_match else 5.0
        
        # 提取一句话评价
        comment = response.replace(str(score), "").strip()
        if len(comment) > 100:
            comment = comment[:100] + "..."
            
        return {"score": score, "comment": comment}

    async def compare_outputs(
        self, original: str, improved: str, criteria: List[str]
    ) -> Dict[str, Any]:
        """
        比较两个输出的质量

        Args:
            original: 原始输出
            improved: 改进后的输出
            criteria: 比较标准

        Returns:
            Dict[str, Any]: 比较结果
        """
        criteria_text = "\n".join([f"- {c}" for c in criteria])
        
        prompt = f"""请比较以下两个输出的质量：

原始输出：
{original}

改进后的输出：
{improved}

比较标准：
{criteria_text}

请给出：
1. 哪个输出更好（回答"原始"或"改进"）
2. 改进的百分比（如20%）
3. 主要改进点（列出3点）
"""

        response = await self.llm.ask([{"role": "user", "content": prompt}])
        
        # 解析结果
        better = "improved" if "改进" in response[:50] else "original"
        
        # 提取改进百分比
        percent_match = re.search(r"(\d+)%", response)
        improvement_percent = int(percent_match.group(1)) if percent_match else 0
        
        # 提取改进点
        improvements = self._extract_list_items(response)
        
        return {
            "better_version": better,
            "improvement_percent": improvement_percent,
            "key_improvements": improvements[:3],  # 最多取3点
        }
