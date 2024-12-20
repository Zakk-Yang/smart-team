"""Base agent class that defines the interface for all agents"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Dict, Any, Optional
from ..types import AgentResponse


class AgentState(Enum):
    """States that an agent can be in"""
    READY = auto()           # Ready to receive new input
    PROCESSING = auto()      # Processing a task
    COMPLETED = auto()       # Task completed, ready to transfer
    TRANSFERRING = auto()    # In process of transferring


class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, name: str, instructions: str, functions: List = None, **kwargs):
        """Initialize the agent"""
        self.name = name
        self.instructions = instructions
        self.functions = functions or []
        self.state = AgentState.READY
        self._init_client(**kwargs)

    @abstractmethod
    def _init_client(self, **kwargs):
        """Initialize the client - to be implemented by specific agents"""
        pass

    @abstractmethod
    def send_message(self, message: str, is_function_result: bool = False) -> AgentResponse:
        """Send a message to the agent and get a response"""
        pass

    @abstractmethod
    def send_function_results(self, executed_functions: List[str]) -> AgentResponse:
        """Send function execution results back to the agent"""
        pass

    def is_ready(self) -> bool:
        """Check if agent is ready for new input"""
        return self.state == AgentState.READY

    def is_completed(self) -> bool:
        """Check if agent has completed its task"""
        return self.state == AgentState.COMPLETED

    def start_processing(self):
        """Mark agent as processing"""
        self.state = AgentState.PROCESSING

    def complete_task(self):
        """Mark task as completed"""
        self.state = AgentState.COMPLETED

    def start_transfer(self):
        """Mark agent as transferring"""
        self.state = AgentState.TRANSFERRING

    def reset(self):
        """Reset agent to ready state"""
        self.state = AgentState.READY
