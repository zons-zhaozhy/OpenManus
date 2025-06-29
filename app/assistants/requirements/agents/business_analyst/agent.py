"""
业务分析师智能体 - 基于BaseAgent

专注于深度业务分析：
- 业务价值分析
- 用户场景建模
- 流程分析
- 风险识别

支持与其他智能体协作，共享分析结果。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
import json

from app.agent.base import BaseAgent
from app.core.prompts import BUSINESS_ANALYST_SYSTEM_PROMPT
from app.core.types import AgentState, Message
from app.llm import LLM
from app.logger import logger, get_logger
from app.schema import AgentAction, AgentResponse
from app.assistants.requirements.agents.base_requirements_agent import BaseRequirementsAgent

from .analysis import BusinessAnalysis

logger = get_logger(__name__)

class BusinessAnalystAgent(BaseRequirementsAgent):
    """业务分析智能体"""

    def __init__(self, flow_manager):
        """初始化业务分析智能体

        Args:
            flow_manager: 工作流管理器
        """
        super().__init__(flow_manager)
        self.llm = LLM()
        self.agent_name = "business_analyst"
        logger.debug(f"业务分析智能体初始化完成")

    async def clarify_requirements(self, requirement: str, knowledge: Dict[str, Any], code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """实现基类方法，但实际上业务分析智能体主要使用analyze_business方法"""
        logger.warning("业务分析智能体不应直接调用clarify_requirements方法")
        return await self.analyze_business(requirement, {}, knowledge, code_analysis)

    async def analyze_business(self, requirement: str, clarification_result: Dict[str, Any], knowledge: Dict[str, Any], code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析业务需求，评估价值和可行性

        Args:
            requirement: 原始需求文本
            clarification_result: 需求澄清结果
            knowledge: 相关知识库内容
            code_analysis: 相关代码分析结果

        Returns:
            Dict[str, Any]: 业务分析结果
        """
        logger.info(f"开始业务分析: {requirement[:50]}...")

        try:
            # 构建提示词
            prompt = self._build_analysis_prompt(requirement, clarification_result, knowledge, code_analysis)
            logger.debug("构建提示词完成")

            # 调用LLM
            logger.info("调用LLM进行业务分析...")
            response = await asyncio.wait_for(
                self.llm.agenerate(prompt),
                timeout=30
            )
            logger.info("LLM调用完成")

            # 解析响应
            analysis_result = self._parse_analysis_response(response)
            logger.info(f"业务分析完成，识别了 {len(analysis_result.get('key_points', []))} 个关键点")

            return analysis_result
        except asyncio.TimeoutError:
            logger.error("业务分析LLM调用超时")
            return {
                "error": "LLM调用超时",
                "status": "error",
                "key_points": [],
                "business_value": "由于LLM调用超时，无法评估业务价值",
                "summary": "由于LLM调用超时，无法完成业务分析"
            }
        except Exception as e:
            logger.error(f"业务分析过程中出现错误: {str(e)}")
            return {
                "error": str(e),
                "status": "error",
                "key_points": [],
                "business_value": "分析过程中出现错误",
                "summary": f"业务分析过程中出现错误: {str(e)}"
            }

    def _build_analysis_prompt(self, requirement: str, clarification_result: Dict[str, Any], knowledge: Dict[str, Any], code_analysis: Dict[str, Any]) -> str:
        """构建业务分析提示词

        Args:
            requirement: 原始需求文本
            clarification_result: 需求澄清结果
            knowledge: 相关知识库内容
            code_analysis: 相关代码分析结果

        Returns:
            str: 提示词
        """
        # 提取澄清结果摘要
        clarification_summary = clarification_result.get("summary", "未提供澄清摘要")
        clarification_questions = "\n".join([
            f"- {q.get('question', '')}: {q.get('reason', '')}"
            for q in clarification_result.get("questions", [])[:5]
        ])

        # 提取知识库内容摘要
        knowledge_summary = "\n".join([
            f"- {item.get('title', 'Untitled')}: {item.get('content', '')[:200]}..."
            for item in knowledge.get("results", [])[:3]
        ])

        # 提取代码分析摘要
        code_summary = "\n".join([
            f"- {component.get('name', 'Unknown')}: {component.get('description', '')}"
            for component in code_analysis.get("components", [])[:3]
        ])

        # 构建提示词
        prompt = f"""
你是一位经验丰富的业务分析师，负责分析软件需求的业务价值和可行性。请分析以下需求，评估其业务价值，并提供实施建议。

## 原始需求
{requirement}

## 需求澄清结果
{clarification_summary}

## 澄清问题
{clarification_questions}

## 相关知识
{knowledge_summary}

## 相关代码组件
{code_summary}

请完成以下任务：
1. 分析需求的业务价值和重要性
2. 评估需求的可行性和实施难度
3. 识别潜在的业务风险和挑战
4. 提出3-5个关键实施建议
5. 给出业务分析总结

输出格式应为JSON：
```json
{
  "status": "success",
  "key_points": ["关键点1", "关键点2", "关键点3"],
  "business_value": "业务价值评估",
  "feasibility": "可行性评估",
  "risks": ["风险1", "风险2"],
  "recommendations": ["建议1", "建议2", "建议3"],
  "summary": "业务分析总结"
}
```

请确保输出是有效的JSON格式。
"""
        return prompt

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应，提取业务分析结果

        Args:
            response: LLM响应文本

        Returns:
            Dict[str, Any]: 解析后的业务分析结果
        """
        try:
            # 尝试提取JSON部分
            json_str = response

            # 如果响应包含```json和```标记，提取其中的内容
            if "```json" in response and "```" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()

            # 解析JSON
            result = json.loads(json_str)

            # 确保结果包含必要的字段
            if "key_points" not in result:
                result["key_points"] = []
            if "business_value" not in result:
                result["business_value"] = "未提供业务价值评估"
            if "summary" not in result:
                result["summary"] = "未提供业务分析总结"
            if "status" not in result:
                result["status"] = "success"

            return result
        except Exception as e:
            logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回一个基本结构
            return {
                "status": "error",
                "error": f"解析响应失败: {str(e)}",
                "key_points": [],
                "business_value": "无法解析业务价值评估",
                "summary": "无法解析LLM响应"
            }
