from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel


class FunctionType(Enum):
    """Types of functions that can be executed by agents"""

    IS_AGENT: bool = None
    ORCHESTRATOR = "orchestrator"
    EXECUTOR = "executor"
    FIXER = "fixer"
    NONE = "none"


class FunctionCall(BaseModel):
    """Represents a single function call in the response"""

    type: FunctionType
    name: str
    parameters: Dict[str, Any] = {}


class Result(BaseModel):
    """Represents the result of an agent's action or response"""

    text: Optional[str] = None
    function_calls: List[FunctionCall] = []


class BaseAgent(ABC):
    """Base class for all platform-specific agents"""

    def __init__(
        self,
        name: str,
        description: str,
        instructions: str,
        functions: Optional[List[Callable]] = None,
        **kwargs,
    ):
        self.name = name
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
