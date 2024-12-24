"""Anthropic-specific agent implementation"""

from typing import List, Dict, Any
from anthropic import Anthropic
from .base_agent import BaseAgent
from ..types import AgentResponse
from dynamic_agent.utils.function_schema import create_function_schema, SchemaFormat


class AnthropicAgent(BaseAgent):
    def _init_client(self, **kwargs):
        self.model = kwargs.get("model", "claude-3-5-sonnet-20241022")
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError("api_key is required for AnthropicAgent")
        self.client = Anthropic(api_key=api_key)
        self.agent_memory = []

    def _get_tool_schemas(self) -> List[Dict]:
        """Convert functions to Anthropic's tool format"""
        return [
            create_function_schema(func, SchemaFormat.ANTHROPIC)
            for func in self.functions
        ]

    def send_message(self, messages: Dict) -> AgentResponse:
        # Get Agent Tool Schema
        tools = self._get_tool_schemas() if self.functions else []

        # Get response from Claude
        response = self.client.messages.create(
            model=self.model,
            messages=messages,
            max_tokens=8192,
            tools=tools,
        )

        # Get the response texts and the function calls seperately
        text_parts = []
        result = AgentResponse()
        result.function_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

            elif block.type == "tool_use":
                # Check if this exact function call with these parameters has been made before
                func_call = {
                    "name": block.name,
                    "parameters": block.input,
                }
                result.function_calls.append(func_call)

        result.text = " ".join(text_parts) if text_parts else ""
        return result
