"""Base agent class that defines the interface for all agents"""

from typing import List, Callable, Dict, Any
from ..types import AgentResponse

class BaseAgent:
    """Base class for all agents"""

    def __init__(self, name: str, instructions: str, functions: List[Callable] = None, **kwargs):
        """Initialize the agent with a name and optional functions"""
        self.name = name
        self.instructions = instructions
        self.functions = functions or []
        self._init_client(**kwargs)

    def _init_client(self, **kwargs):
        """Initialize any client-specific resources"""
        pass

    def send_message(self, message: str) -> AgentResponse:
        """Send a message to the agent and get a response"""
        raise NotImplementedError("Subclasses must implement send_message")
