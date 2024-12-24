"""OpenAI-specific agent implementation"""

from typing import List, Dict, Any
import json
from openai import OpenAI
from .base_agent import BaseAgent
from ..types import AgentResponse
from dynamic_agent.utils.function_schema import create_function_schema, SchemaFormat


class OpenAIAgent(BaseAgent):
    def _init_client(self, **kwargs):
        self.model = kwargs.get("model", "gpt-4-1106-preview")
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError("api_key is required for OpenAIAgent")
        self.client = OpenAI(api_key=api_key)
        self.agent_memory = []

    def _get_tool_schemas(self) -> List[Dict]:
        """Convert functions to OpenAI's tool format"""
        return [
            {
                "type": "function",
                "function": create_function_schema(func, SchemaFormat.OPENAI),
            }
            for func in self.functions
        ]

    def send_message(self, messages: Dict) -> AgentResponse:
        # Get Agent Tool Schema
        tools = self._get_tool_schemas() if self.functions else []

        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        # Process the response
        result = AgentResponse()
        result.function_calls = []

        message = response.choices[0].message
        result.text = message.content or ""

        # Handle tool calls if present
        if message.tool_calls:
            for tool_call in message.tool_calls:
                # Parse the arguments from JSON string to dict
                try:
                    parameters = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    parameters = {}

                func_call = {
                    "name": tool_call.function.name,
                    "parameters": parameters,
                }
                result.function_calls.append(func_call)

        return result
