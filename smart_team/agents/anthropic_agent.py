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
        tools = self._get_tool_schemas() if self.functions else []

        # Store the main task if this is not a function result
        if not is_function_result:
            self.current_task = message
            self.error_context = None  # Reset error context for new tasks

        # Add user message to history
        self.messages.append({"role": "user", "content": message})

        # Build system message with instructions and completed functions
        system_message = self.instructions
        if self.completed_function_calls:
            # Format completed function calls with their parameters
            completed_calls = [
                f"{call['name']}({', '.join(f'{k}={v}' for k, v in call['parameters'].items())})"
                for call in self.completed_function_calls
            ]
            system_message += f"\n\nPreviously executed function calls: {', '.join(completed_calls)}"
        if self.error_context:
            system_message += f"\n\nError Context: {self.error_context}"
            system_message += "\nPlease fix this error by installing any missing packages or fixing code issues."
            if "ModuleNotFoundError: No module named" in self.error_context:
                # Extract module name from error
                module_name = self.error_context.split("'")[1].split(".")[0]
                system_message += f"\nAction Required: Install missing module '{module_name}' using install_package function."

        response = self.client.messages.create(
            model=self.model,
            system=system_message,
            messages=[
                msg for msg in self.messages if msg["role"] != "system"
            ],  # Filter out system messages
            max_tokens=8192,
            tools=tools,
        )

        text_parts = []
        result = AgentResponse()
        result.function_calls = []  # Initialize as empty list instead of None

        # Process each content block
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                # Skip if function was already completed and we're not handling an error
                if block.name in [call["name"] for call in self.completed_function_calls] and not self.error_context:
                    continue
                # Add function call information
                result.function_calls.append(
                    {
                        "name": block.name,
                        "parameters": block.input,
                    }
                )

        # If we have an error context but no function calls were added, add appropriate function call
        if self.error_context and not result.function_calls:
            if "ModuleNotFoundError: No module named" in self.error_context:
                module_name = self.error_context.split("'")[1].split(".")[0]
                result.function_calls.append(
                    {
                        "name": "install_package",
                        "parameters": {
                            "env_name": "stock_analysis",  # Use the current env name
                            "package": module_name,
                        },
                    }
                )

        # Combine all text parts
        result.text = " ".join(text_parts) if text_parts else None

        # Add assistant response to history
        self.messages.append({"role": "assistant", "content": result.text})

        return result

    def send_function_results(self, executed_functions: list[str]) -> AgentResponse:
        """Send function execution results back to the agent"""
        if not executed_functions:
            return AgentResponse()

        function_results = "\n".join(executed_functions)

        # Check for errors in function results
        error_found = False
        for result in executed_functions:
            if "Error:" in result or "ModuleNotFoundError:" in result:
                error_found = True
                self.error_context = result
                continue

            # Track completed functions
            if result.startswith("Function "):
                func_name = result.split()[1]
                for call in self.completed_function_calls:
                    if call["name"] == func_name:
                        break
                else:
                    self.completed_function_calls.append({
                        "name": func_name,
                        "parameters": {}
                    })

        message = f"The following functions have been executed:\n{function_results}\n\n"

        # Send the message and get response
        return self.send_message(message, is_function_result=True)

    def add_completed_function(self, func_name: str, parameters: dict):
        """Track completed function calls with their parameters"""
        self.completed_function_calls.append({
            "name": func_name,
            "parameters": parameters
        })
