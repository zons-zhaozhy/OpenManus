from typing import Dict, Any, Optional
from app.llm import LLM
from app.schema import Message, Memory

class AnalysisAgent:
    def __init__(self):
        self.memory = Memory()
        self.prompt = """
        你是一个需求分析助手，负责深入分析用户的需求。
        你的目标是识别关键功能、约束条件和技术要求。
        如果需要更多信息，请提出问题。
        当你认为已经完成了全面分析时，请返回一个包含"status": "complete"的结果。
        """

    async def analyze(self, clarification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the clarified requirements."""
        input_text = f"分析以下澄清的需求：{clarification_data}"
        self.memory.add_message(Message.user_message(input_text))

        system_message = Message.system_message(self.prompt)
        self.memory.add_message(system_message)

        llm = LLM()
        messages = self.memory.to_dict_list()
        # Temporary ignore type error due to mismatch in expected type
        response = await llm.ask(messages=messages)  # type: ignore
        self.memory.add_message(Message.assistant_message(response))

        # Simple logic to determine if analysis is complete
        if "complete" in response.lower():
            return {"status": "complete", "analysis_result": response}
        else:
            return {"status": "in_progress", "questions": response}

    async def process_input(self, user_input: str, clarification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input during the analysis stage."""
        input_text = f"用户输入：{user_input}\n澄清的需求：{clarification_data}"
        self.memory.add_message(Message.user_message(input_text))

        system_message = Message.system_message(self.prompt)
        self.memory.add_message(system_message)

        llm = LLM()
        messages = self.memory.to_dict_list()
        # Temporary ignore type error due to mismatch in expected type
        response = await llm.ask(messages=messages)  # type: ignore
        self.memory.add_message(Message.assistant_message(response))

        # Simple logic to determine if analysis is complete
        if "complete" in response.lower():
            return {"status": "complete", "analysis_result": response}
        else:
            return {"status": "in_progress", "questions": response}
