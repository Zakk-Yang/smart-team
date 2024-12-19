from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Literal, Optional, Any
from enum import Enum
from pydantic import BaseModel
from smart_team.types import Result


class BaseAgent(ABC):
    """Base class for all platform-specific agents"""

    def __init__(
        self,
        name: str,
        description: str,
        instructions: str,
        functions: Optional[List[Callable]] = None,
        agent_type: Optional[Literal["orchestrator", "executor", "fixer"]] = None,
        **kwargs,
    ):
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.instructions = instructions
        self.functions = functions or []
        self._init_client(**kwargs)

    @abstractmethod
    def _init_client(self, **kwargs):
        """Initialize the platform-specific client"""
        pass

    @abstractmethod
    def _get_tool_schemas(self) -> List[Dict]:
        """Get platform-specific function schemas"""
        pass

    @abstractmethod
    def send_message(self, message: str) -> Result:
        """Send a message to the agent and get the response"""
        pass
