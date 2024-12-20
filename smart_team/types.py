"""
Module: types.py
Purpose: Define common types and data structures used throughout the project
"""

from __future__ import annotations
from dataclasses import dataclass
from typing_extensions import TypedDict

@dataclass
class AgentResponse:
    """Response from an agent"""
    text: str | None = None
    function_calls: list[dict[str, any]] | None = None
