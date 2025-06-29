import json

from app.tool import BaseTool


class AskHuman(BaseTool):
    """Use this tool to ask human for help."""

    name: str = "ask_human"
    description: str = "Use this tool to ask human for help."
    parameters: str = json.dumps(
        {
            "type": "object",
            "properties": {
                "inquire": {
                    "type": "string",
                    "description": "The question you want to ask human.",
                },
                "request_id": {
                    "type": "string",
                    "description": "A unique ID for this interaction request.",
                    "default": "",
                },
            },
            "required": ["inquire"],
        }
    )

    async def execute(self, inquire: str, request_id: str = "") -> str:
        """
        Signals to the orchestrator that human input is required.
        This tool does not directly block or get input itself.
        The orchestrator is responsible for handling this signal,
        prompting the user via the frontend, and feeding the response back.
        """
        # Return a structured JSON string that the orchestrator/frontend can interpret
        return json.dumps(
            {
                "tool_name": self.name,
                "type": "human_input_required",
                "question": inquire,
                "request_id": request_id,
            }
        )
