"""Anthropic-specific agent implementation"""

from typing import List, Dict, Any
from anthropic import Anthropic
from .base_agent import BaseAgent
from ..types import AgentResponse
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
        self.messages = []  # Store conversation history
        self.completed_function_calls = []  # Track completed function calls with parameters
        self.current_task = None  # Store current task
        self.error_context = None  # Store error context for self-correction
        self.returning_to_orchestrator = False  # Flag to track returns to orchestrator

    def _get_tool_schemas(self) -> List[Dict]:
        """Convert functions to Anthropic's tool format"""
        return [
            create_function_schema(func, SchemaFormat.ANTHROPIC)
            for func in self.functions
        ]

    def send_message(
        self, message: str, is_function_result: bool = False
    ) -> AgentResponse:
        """Send a message to Claude and process the response"""
        if not message.strip():
            return AgentResponse(text="", function_calls=[])

        # If we're the orchestrator and we're returning from another agent
        if self.name == "OrchestratorBot" and self.returning_to_orchestrator:
            self.returning_to_orchestrator = False
            return AgentResponse(
                text="What would you like to do next?",
                function_calls=[]
            )

        tools = self._get_tool_schemas() if self.functions else []

        if not is_function_result:
            self.current_task = message
            self.error_context = None

        # Add user message to history
        self.messages.append({"role": "user", "content": message})

        # Filter out empty messages and system messages
        valid_messages = [
            msg for msg in self.messages
            if msg["role"] != "system" and msg.get("content", "").strip()
        ]

        if not valid_messages:
            return AgentResponse(text="", function_calls=[])

        # Build system message
        system_message = self.instructions
        if self.completed_function_calls:
            completed_calls = [
                f"{call['name']}({', '.join(f'{k}={v}' for k, v in call['parameters'].items())})"
                for call in self.completed_function_calls
            ]
            system_message += f"\n\nPreviously executed function calls: {', '.join(completed_calls)}"

        if self.error_context:
            system_message += f"\n\nError Context: {self.error_context}"
            system_message += "\nPlease handle this error appropriately."

        # Get response from Claude
        response = self.client.messages.create(
            model=self.model,
            system=system_message,
            messages=valid_messages,
            max_tokens=8192,
            tools=tools,
        )

        # Process response
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
                if not any(
                    call["name"] == func_call["name"] and call["parameters"] == func_call["parameters"]
                    for call in self.completed_function_calls
                ) or self.error_context:
                    result.function_calls.append(func_call)

        result.text = " ".join(text_parts) if text_parts else ""
        if result.text.strip():  # Only add non-empty responses to history
            self.messages.append({"role": "assistant", "content": result.text})
        return result

    def send_function_results(self, executed_functions: list[str]) -> AgentResponse:
        """Send function execution results back to the agent"""
        if not executed_functions:
            return AgentResponse(text="", function_calls=[])

        function_results = "\n".join(f"- {func}" for func in executed_functions)

        # For orchestrator, just wait for next input
        if self.name == "OrchestratorBot":
            self.returning_to_orchestrator = False
            return AgentResponse(
                text="What would you like to do next?",
                function_calls=[]
            )

        # For other agents, check if we need to return to orchestrator
        message = f"The following functions have been executed:\n{function_results}"
        if "transfer_to_orchestrator" in [call["name"] for call in self.completed_function_calls]:
            self.returning_to_orchestrator = True
            return AgentResponse(text="", function_calls=[])
        
        return self.send_message(message, is_function_result=True)

    def add_completed_function(self, func_name: str, parameters: dict):
        """Track completed function calls with their parameters"""
        self.completed_function_calls.append(
            {"name": func_name, "parameters": parameters}
        )
