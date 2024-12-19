from smart_team.agents.anthropic_agent import AnthropicAgent
from dotenv import load_dotenv
import os


def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
