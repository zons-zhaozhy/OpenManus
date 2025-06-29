"""
业务分析相关的方法集合
"""

from typing import Dict, List, Optional

from app.core.prompts import (
    BUSINESS_VALUE_ANALYSIS_PROMPT,
    USER_SCENARIO_ANALYSIS_PROMPT,
)
from app.llm import LLM
from app.logger import logger


class BusinessAnalysis:
    """业务分析工具类"""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def analyze_business_value(self, messages: List[Dict]) -> str:
        """分析业务价值"""
        messages = messages + [
            {"role": "system", "content": BUSINESS_VALUE_ANALYSIS_PROMPT}
        ]
        response = await self.llm.ask(messages, temperature=0.3)
        logger.info("完成业务价值分析")
        return response

    async def analyze_user_scenarios(self, messages: List[Dict]) -> str:
        """分析用户场景"""
        messages = messages + [
            {"role": "system", "content": USER_SCENARIO_ANALYSIS_PROMPT}
        ]
        response = await self.llm.ask(messages, temperature=0.3)
        logger.info("完成用户场景分析")
        return response

    async def analyze_business_process(self, requirement: str) -> Dict:
        """分析业务流程"""
        prompt = self._build_process_analysis_prompt(requirement)
        response = await self.llm.ask([{"role": "system", "content": prompt}])
        return self._parse_process_analysis(response)

    async def extract_business_rules(self, process_analysis: Dict) -> List[Dict]:
        """提取业务规则"""
        prompt = self._build_rules_extraction_prompt(process_analysis)
        response = await self.llm.ask([{"role": "system", "content": prompt}])
        return self._parse_business_rules(response)

    async def assess_business_value(
        self, requirement: str, process_analysis: Dict, rules: List[Dict]
    ) -> Dict:
        """评估业务价值"""
        prompt = self._build_value_assessment_prompt(
            requirement, process_analysis, rules
        )
        response = await self.llm.ask([{"role": "system", "content": prompt}])
        return self._parse_value_assessment(response)

    async def assess_risks(
        self, process_analysis: Dict, rules: List[Dict], value_assessment: Dict
    ) -> Dict:
        """评估风险"""
        prompt = self._build_risk_assessment_prompt(
            process_analysis, rules, value_assessment
        )
        response = await self.llm.ask([{"role": "system", "content": prompt}])
        return self._parse_risk_assessment(response)

    def _build_process_analysis_prompt(self, requirement: str) -> str:
        return f"""请分析以下需求的业务流程：

需求内容：
{requirement}

请提供：
1. 当前流程（As-Is）
2. 目标流程（To-Be）
3. 关键优化点
4. 实施建议"""

    def _build_rules_extraction_prompt(self, process_analysis: Dict) -> str:
        return """请从业务流程中提取关键业务规则：

1. 数据规则
2. 流程规则
3. 计算规则
4. 约束条件
5. 异常处理规则"""

    def _build_value_assessment_prompt(
        self, requirement: str, process_analysis: Dict, rules: List[Dict]
    ) -> str:
        return """请评估业务价值：

1. 直接价值
2. 间接价值
3. 长期价值
4. ROI分析
5. 成本效益分析"""

    def _build_risk_assessment_prompt(
        self, process_analysis: Dict, rules: List[Dict], value_assessment: Dict
    ) -> str:
        return """请评估实施风险：

1. 业务风险
2. 技术风险
3. 运营风险
4. 合规风险
5. 风险缓解策略"""

    def _parse_process_analysis(self, response: str) -> Dict:
        """解析业务流程分析结果"""
        # TODO: 实现具体的解析逻辑
        return {"raw_response": response}

    def _parse_business_rules(self, response: str) -> List[Dict]:
        """解析业务规则"""
        # TODO: 实现具体的解析逻辑
        return [{"rule": response}]

    def _parse_value_assessment(self, response: str) -> Dict:
        """解析价值评估结果"""
        # TODO: 实现具体的解析逻辑
        return {"assessment": response}

    def _parse_risk_assessment(self, response: str) -> Dict:
        """解析风险评估结果"""
        # TODO: 实现具体的解析逻辑
        return {"risks": response}
