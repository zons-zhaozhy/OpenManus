from typing import Dict, Any, Optional
from app.llm import LLM
from app.schema import Message, Memory

class DocumentationAgent:
    def __init__(self):
        self.memory = Memory()
        self.prompt = """
        你是一个需求文档生成助手，负责根据分析结果生成详细的需求文档。
        你的目标是创建清晰、结构化的文档，包含所有必要的信息。
        如果需要更多信息或有任何不明确的地方，请提出问题。
        当你认为已经生成了完整的文档时，请返回一个包含"status": "complete"的结果。
        """

    async def generate_documentation(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate documentation based on analysis results."""
        input_text = f"根据以下分析结果生成需求文档：{analysis_data}"
        self.memory.add_message(Message.user_message(input_text))

        system_message = Message.system_message(self.prompt)
        self.memory.add_message(system_message)

        llm = LLM()
        messages = self.memory.to_dict_list()
        # Temporary ignore type error due to mismatch in expected type
        response = await llm.ask(messages=messages)  # type: ignore
        self.memory.add_message(Message.assistant_message(response))

        # Simple logic to determine if documentation is complete
        if "complete" in response.lower():
            return {"status": "complete", "documentation": response}
        else:
            return {"status": "in_progress", "questions": response}

    async def process_input(self, user_input: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input during the documentation stage."""
        input_text = f"用户输入：{user_input}\n分析结果：{analysis_data}"
        self.memory.add_message(Message.user_message(input_text))

        system_message = Message.system_message(self.prompt)
        self.memory.add_message(system_message)

        llm = LLM()
        messages = self.memory.to_dict_list()
        # Temporary ignore type error due to mismatch in expected type
        response = await llm.ask(messages=messages)  # type: ignore
        self.memory.add_message(Message.assistant_message(response))

        # Simple logic to determine if documentation is complete
        if "complete" in response.lower():
            return {"status": "complete", "documentation": response}
        else:
            return {"status": "in_progress", "questions": response}
