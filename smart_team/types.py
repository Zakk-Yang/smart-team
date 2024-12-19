"""Core type definitions for the smart team framework.

This module defines the fundamental data structures and types used throughout the framework
for representing function types, function calls, and agent results. These types provide
a standardized way to handle agent interactions and their responses.

Classes:
    FunctionType: Defines the type and behavior of functions in the agent system
    FunctionCall: Represents a single function call made by an agent
    Result: Standardized container for agent responses and function calls
"""

from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel


class FunctionType(BaseModel):
    """Defines the type and behavior of a function in the agent system.

    Attributes:
        is_agent: Whether this function represents an agent operation
        function_type: The type of function - either "transfer" for agent handoffs or "tool" for utility functions
        agent_type: The specific type of agent if is_agent is True - can be orchestrator, executor, fixer, or evaluator
    """

    is_agent: bool
    function_type: Optional[Literal["transfer", "tool"]]
    agent_type: Optional[Literal["orchestrator", "executor", "fixer", "evaluator"]]


class FunctionCall(BaseModel):
    """Represents a single function call made by an agent.

    Attributes:
        name: The name of the function being called
        parameters: Dictionary of parameters passed to the function
        function_type: List of function types that describe this call's behavior
    """

    name: str
    parameters: Dict[str, Any] = {}
    function_type: Optional[List[FunctionType]] = None


class Result(BaseModel):
    """Represents the result of an agent's action or response.

    A standardized container for agent responses that can include both text output
    and a list of function calls that were made during processing.

    Attributes:
        text: The text response from the agent, if any
        function_calls: List of function calls made by the agent during processing
    """

    text: Optional[str] = None
    function_calls: Optional[List[FunctionCall]] = None
