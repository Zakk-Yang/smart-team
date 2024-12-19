"""Agent implementations for the Smart Team Framework.

This module provides various agent implementations including:
- BaseAgent: Abstract base class defining the agent interface
- AnthropicAgent: Implementation using Anthropic's Claude model
"""

from smart_team.agents.base_agent import BaseAgent
from smart_team.agents.anthropic_agent import AnthropicAgent

__all__ = ["BaseAgent", "AnthropicAgent"]
