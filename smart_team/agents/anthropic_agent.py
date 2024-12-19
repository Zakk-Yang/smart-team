from anthropic import Anthropic
from typing import Dict, List
from smart_team.types import Result, FunctionCall
from smart_team.agents.base_agent import BaseAgent
from dynamic_agent.utils.function_schema import create_function_schema, SchemaFormat


class AnthropicAgent(BaseAgent):
    """Implementation of BaseAgent for the Anthropic platform"""

    def _init_client(self, **kwargs):
        """Initialize the Anthropic client"""
        self.model = kwargs.get("model", "claude-3-5-sonnet-20241022")
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError("api_key is required for AnthropicAgent")
        self.client = Anthropic(api_key=api_key)

    def _get_tool_schemas(self) -> List[Dict]:
        """Convert functions to Anthropic's tool format"""
        return [
            create_function_schema(func, SchemaFormat.ANTHROPIC)
            for func in self.functions
        ]

    def send_message(self, message: str) -> Result:
        """Send a message to Claude and process the response"""
        tools = self._get_tool_schemas() if self.functions else []

        response = self.client.messages.create(
            model=self.model,
            system=self.instructions,
            messages=[{"role": "user", "content": message}],
            max_tokens=1024,
            tools=tools,
        )

        result = Result()
        text_parts = []

        # Process each content block
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                # Add function call information
                result.function_calls.append(
                    FunctionCall(
                        function_type=(
                            "transfer"
                            if block.name.startswith("transfer_to_")
                            else "tool"
                        ),
                        name=block.name,
                        parameters=block.input,
                    )
                )

        # Combine all text parts
        result.text = " ".join(text_parts) if text_parts else None

        return result
