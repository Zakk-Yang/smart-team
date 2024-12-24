"""Ollama-specific agent implementation"""

from typing import List, Dict, Any
import json
import ollama
from .base_agent import BaseAgent
from ..types import AgentResponse
from dynamic_agent.utils.function_schema import create_function_schema, SchemaFormat


class OllamaAgent(BaseAgent):
    def _init_client(self, **kwargs):
        """Initialize the Ollama client"""
        self.model = kwargs.get("model", "llama2")
        self.api_key = kwargs.get("api_key")  # Not used by Ollama but kept for API consistency
        self.client = ollama.Client(host=kwargs.get("base_url", "http://localhost:11434"))
        self.agent_memory = []

    def _transform_messages(self, messages: List[Dict]) -> List[Dict]:
        """Transform messages to Ollama format while preserving original structure"""
        if not isinstance(messages, list):
            messages = [messages]
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def _transform_tools(self, tools: List[Dict]) -> List[Dict]:
        """Transform tools to Ollama format while preserving original structure"""
        return tools  # Ollama accepts OpenAI format, so no transformation needed

    def _transform_response(self, response) -> Dict:
        """Transform Ollama response to standard format"""
        return {
            "content": response.message.content or "",
            "tool_calls": response.message.tool_calls or [],
        }

    def _get_tool_schemas(self) -> List[Dict]:
        """Convert functions to Ollama's tool format"""
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

        # Transform messages and tools to Ollama format
        ollama_messages = self._transform_messages(messages)

        try:
            # Send request to Ollama
            response = self.client.chat(
                model=self.model,
                messages=ollama_messages,
                tools=tools,
            )
            response_data = self._transform_response(response)
        except Exception as e:
            return AgentResponse(text=f"Error: {str(e)}", function_calls=[])

        # Process the response
        result = AgentResponse()
        result.text = response_data["content"]
        result.function_calls = []

        # Handle tool calls if present
        for tool_call in response_data.get("tool_calls", []):
            try:
                parameters = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, AttributeError, TypeError):
                parameters = {}

            func_call = {
                "name": tool_call.function.name,
                "parameters": parameters,
            }
            result.function_calls.append(func_call)

        return result
