"""Base agent class that defines the interface for all agents"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..types import AgentResponse


class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, name: str, instructions: str, functions: List = None, **kwargs):
        """Initialize the agent"""
        self.is_ochestrator: bool = False
        self.name = name
        self.instructions = instructions
        self.functions = functions or []
        self._init_client(**kwargs)

    @abstractmethod
    def _init_client(self, **kwargs):
        """Initialize the client - to be implemented by specific agents"""
        pass

    @abstractmethod
    def send_message(
        self, message: str, is_function_result: bool = False
    ) -> AgentResponse:
        """Send a message to the agent and get a response"""
        pass
