"""
Think Tool - 结构化思维工具
实现深度推理和分步骤思考机制，提升智能体智能化程度

参考：
- Anthropic Think Tool机制
- Chain-of-Thought推理
- 自我反思和迭代改进
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.llm import LLM
from app.logger import logger


class ThinkingPhase(Enum):
    """思维阶段枚举"""

    UNDERSTANDING = "understanding"  # 理解阶段
    ANALYSIS = "analysis"  # 分析阶段
    PLANNING = "planning"  # 规划阶段
    REASONING = "reasoning"  # 推理阶段
    EVALUATION = "evaluation"  # 评估阶段


@dataclass
class ThinkingStep:
    """思维步骤数据结构"""

    phase: ThinkingPhase
    content: str
    confidence: float = 0.0
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ThinkingResult:
    """思维结果数据结构"""

    steps: List[ThinkingStep]
    summary: str
    confidence: float
    reasoning_chain: List[str]
    insights: List[str]
    next_actions: List[str]


class ThinkTool:
    """
    Think Tool - 结构化思维工具

    实现深度推理机制，让智能体能够：
    1. 分步骤思考问题
    2. 进行结构化分析
    3. 生成推理链
    4. 自我评估和反思
    """

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm or LLM(config_name="think_tool")
        self.thinking_templates = self._load_thinking_templates()

    def _load_thinking_templates(self) -> Dict[str, str]:
        """加载思维模板"""
        return {
            "understanding": """
深入理解问题：
1. 问题的核心是什么？
2. 涉及哪些关键要素？
3. 有什么隐含的假设或约束？
4. 预期的输出是什么？
""",
            "analysis": """
系统性分析：
1. 将问题分解为子问题
2. 识别关键挑战和风险点
3. 分析可用资源和约束条件
4. 评估不同方案的可行性
""",
            "planning": """
制定解决方案：
1. 设计总体解决策略
2. 制定详细执行步骤
3. 识别关键里程碑
4. 准备应急方案
""",
            "reasoning": """
深度推理：
1. 基于已知信息进行逻辑推导
2. 考虑多种可能的情况
3. 评估各种方案的优缺点
4. 得出初步结论
""",
            "evaluation": """
自我评估：
1. 检查推理过程的逻辑性
2. 评估结论的可信度
3. 识别潜在的盲点或错误
4. 提出改进建议
""",
        }

    async def structured_thinking(
        self,
        problem: str,
        context: Optional[Dict] = None,
        phases: Optional[List[ThinkingPhase]] = None,
    ) -> ThinkingResult:
        """
        结构化思维主流程

        Args:
            problem: 需要思考的问题
            context: 上下文信息
            phases: 指定的思维阶段，默认执行所有阶段

        Returns:
            思维结果
        """
        logger.info(f"🧠 开始结构化思维: {problem[:100]}...")

        # 默认执行所有思维阶段
        if phases is None:
            phases = list(ThinkingPhase)

        thinking_steps = []
        reasoning_chain = []

        # 逐阶段思考
        for phase in phases:
            step = await self._think_in_phase(problem, phase, context, thinking_steps)
            thinking_steps.append(step)
            reasoning_chain.append(f"{phase.value}: {step.content}")

            logger.info(f"  ✓ 完成{phase.value}阶段思考，置信度: {step.confidence:.2f}")

        # 生成思维总结
        summary = await self._generate_summary(problem, thinking_steps)

        # 提取洞察和下一步行动
        insights = await self._extract_insights(thinking_steps)
        next_actions = await self._suggest_next_actions(thinking_steps)

        # 计算整体置信度
        overall_confidence = sum(step.confidence for step in thinking_steps) / len(
            thinking_steps
        )

        result = ThinkingResult(
            steps=thinking_steps,
            summary=summary,
            confidence=overall_confidence,
            reasoning_chain=reasoning_chain,
            insights=insights,
            next_actions=next_actions,
        )

        logger.info(f"🎯 思维过程完成，整体置信度: {overall_confidence:.2f}")
        return result

    async def _think_in_phase(
        self,
        problem: str,
        phase: ThinkingPhase,
        context: Optional[Dict],
        previous_steps: List[ThinkingStep],
    ) -> ThinkingStep:
        """在特定阶段进行思考"""

        # 构建上下文
        phase_context = self._build_phase_context(
            problem, phase, context, previous_steps
        )

        # 生成思维内容
        thinking_prompt = self._create_thinking_prompt(phase, phase_context)
        response = await self.llm.ask([{"role": "user", "content": thinking_prompt}])

        # 评估置信度
        confidence = await self._evaluate_confidence(phase, response)

        # 构建思维步骤
        step = ThinkingStep(
            phase=phase,
            content=response.strip(),
            confidence=confidence,
            metadata={
                "timestamp": asyncio.get_event_loop().time(),
                "context_used": phase_context is not None,
            },
        )

        return step

    def _build_phase_context(
        self,
        problem: str,
        phase: ThinkingPhase,
        context: Optional[Dict],
        previous_steps: List[ThinkingStep],
    ) -> str:
        """构建阶段上下文"""
        context_parts = [f"问题: {problem}"]

        # 添加外部上下文
        if context:
            context_parts.append(f"上下文信息: {context}")

        # 添加之前的思考步骤
        if previous_steps:
            previous_thinking = "\n".join(
                [f"{step.phase.value}: {step.content}" for step in previous_steps]
            )
            context_parts.append(f"之前的思考:\n{previous_thinking}")

        return "\n\n".join(context_parts)

    def _create_thinking_prompt(self, phase: ThinkingPhase, context: str) -> str:
        """创建思维提示词"""
        template = self.thinking_templates.get(phase.value, "")

        prompt = f"""
作为一个专业的需求分析师，请进行{phase.value}阶段的深度思考。

{context}

请按照以下思考框架进行分析：
{template}

要求：
1. 思考要深入、全面
2. 逻辑要清晰、严谨
3. 结论要明确、可行
4. 考虑多种可能性和潜在风险

请提供你的{phase.value}结果：
"""
        return prompt

    async def _evaluate_confidence(self, phase: ThinkingPhase, content: str) -> float:
        """评估思考内容的置信度"""
        confidence_prompt = f"""
请评估以下{phase.value}阶段思考内容的质量和置信度：

内容：
{content}

评估标准：
1. 逻辑性和连贯性 (0-1分)
2. 深度和全面性 (0-1分)
3. 实用性和可行性 (0-1分)
4. 专业性和准确性 (0-1分)

请只返回一个0-1之间的数值，代表整体置信度：
"""

        try:
            response = await self.llm.ask(
                [{"role": "user", "content": confidence_prompt}]
            )
            confidence = float(response.strip())
            return max(0.0, min(1.0, confidence))  # 确保在0-1范围内
        except:
            return 0.7  # 默认置信度

    async def _generate_summary(self, problem: str, steps: List[ThinkingStep]) -> str:
        """生成思维总结"""
        all_thinking = "\n\n".join(
            [
                f"**{step.phase.value}阶段** (置信度: {step.confidence:.2f}):\n{step.content}"
                for step in steps
            ]
        )

        summary_prompt = f"""
问题: {problem}

完整思考过程:
{all_thinking}

请生成一个简洁而全面的总结，包括：
1. 核心发现和洞察
2. 主要结论
3. 关键决策要点

总结：
"""

        return await self.llm.ask([{"role": "user", "content": summary_prompt}])

    async def _extract_insights(self, steps: List[ThinkingStep]) -> List[str]:
        """提取关键洞察"""
        all_content = "\n".join([step.content for step in steps])

        insights_prompt = f"""
从以下思考内容中提取3-5个关键洞察：

{all_content}

请以简洁的要点形式列出最重要的洞察，每个洞察一行：
"""

        response = await self.llm.ask([{"role": "user", "content": insights_prompt}])
        insights = [line.strip() for line in response.split("\n") if line.strip()]
        return insights[:5]  # 最多5个洞察

    async def _suggest_next_actions(self, steps: List[ThinkingStep]) -> List[str]:
        """建议下一步行动"""
        all_content = "\n".join([step.content for step in steps])

        actions_prompt = f"""
基于以下思考内容，建议3-5个具体的下一步行动：

{all_content}

请提供可执行的、具体的行动建议，每个行动一行：
"""

        response = await self.llm.ask([{"role": "user", "content": actions_prompt}])
        actions = [line.strip() for line in response.split("\n") if line.strip()]
        return actions[:5]  # 最多5个行动

    async def quick_think(self, question: str) -> str:
        """快速思考模式 - 用于简单问题"""
        thinking_prompt = f"""
请对以下问题进行快速而深入的思考：

{question}

思考要求：
1. 首先理解问题的核心
2. 分析关键要素和约束
3. 提出解决方案
4. 评估方案的可行性

请提供你的思考结果：
"""

        return await self.llm.ask([{"role": "user", "content": thinking_prompt}])

    def get_thinking_quality_score(self, result: ThinkingResult) -> Dict[str, float]:
        """获取思维质量评分"""
        return {
            "overall_confidence": result.confidence,
            "completeness": len(result.steps) / len(ThinkingPhase),
            "depth": sum(len(step.content.split()) for step in result.steps)
            / len(result.steps),
            "actionability": len(result.next_actions) / 5.0,
            "insight_quality": len(result.insights) / 5.0,
        }
