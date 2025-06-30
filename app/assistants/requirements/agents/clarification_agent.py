from typing import Dict, Any, Optional
from app.llm import LLM
from app.schema import Message, Memory

class ClarificationAgent:
    def __init__(self):
        self.memory = Memory()
        self.prompt = """
        你是一个需求澄清助手，负责与用户互动以澄清他们的需求。
        你的目标是确保完全理解用户的需求、目标和约束条件。
        如果有任何不明确的地方，请提出问题以获取更多信息。
        当你认为已经充分理解了用户的需求时，请返回一个包含"status": "complete"的结果。
        """

    async def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input to clarify requirements."""
        if user_input:
            self.memory.add_message(Message.user_message(user_input))

        system_message = Message.system_message(self.prompt)
        self.memory.add_message(system_message)

        llm = LLM()
        messages = self.memory.to_dict_list()
        # Temporary ignore type error due to mismatch in expected type
        response = await llm.ask(messages=messages)  # type: ignore
        self.memory.add_message(Message.assistant_message(response))

        # Simple logic to determine if clarification is complete
        if "complete" in response.lower():
            return {"status": "complete", "clarified_requirements": response}
        else:
            return {"status": "in_progress", "questions": response}
