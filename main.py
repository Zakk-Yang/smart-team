"""Main entry point for the agent framework"""

from enum import Enum, auto
from anthropic import Anthropic
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
from dynamic_agent.utils.function_schema import create_function_schema, SchemaFormat
from smart_team.agents.agent_functions import (
    create_virtualenv,
    install_package,
    execute_code,
    get_weather,
    search_and_fetch_content,
)
from smart_team.agents.base_agent import BaseAgent
from smart_team.agents.anthropic_agent import AnthropicAgent
from smart_team.agents.openai_agent import OpenAIAgent


def transfer_to_weather(task: str) -> BaseAgent:
    """Transfer control to the weather bot
    Args:
        task (str, optional): Give the weather bot the task.
    """
    return weather_bot


def transfer_to_search(task: str) -> BaseAgent:
    """Transfer control to the search bot
    Args:
        task (str, optional): Give the search bot the task.
    """
    return search_bot


def transfer_to_orchestrator(task: str) -> BaseAgent:
    """Transfer control back to the ochestrator when assigned tasks are done or need additional supports
    Args:
        task (str, optional): Update the ochestrator what have been done and what errors have been made.
    """
    return orchestrator


def transfer_to_code(task: str) -> BaseAgent:
    """Transfer control to the code bot
    Args:
        task (str, optional): Give the code bot the task.
    """
    return code_bot


# Initialize the weather bot
weather_bot = OpenAIAgent(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    name="WeatherBot",
    instructions="""
    You are the weather bot. Your role is to:
    1. Get weather information for specified locations
    2. After completing the task, return control to orchestrator
    3. DO NOT suggest additional weather checks unless asked by the user
    4. Initiaite multiple functions in the same result
    """,
    functions=[get_weather, transfer_to_orchestrator],
)

# Initialize the weather bot
search_bot = OpenAIAgent(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    name="SearchBot",
    instructions="""
    You are the Search bot. Your role is to:
    1. Get required information using search_and_fetch_content function
    2. For multiple search quries, execute the function multiple times
    3. After completing the task, return control to orchestrator
    """,
    functions=[search_and_fetch_content, transfer_to_orchestrator],
)


# Initialize the code bot
code_bot = AnthropicAgent(
    name="CodeBot",
    model="claude-3-5-sonnet-20241022",
    instructions="""
    You are the coding assistant. Your role is to:
    1. Help users with coding tasks and questions
    2. Create env (stick to the env name as python_env), install packages, generate and debug code
    3. Initiaite multiple functions in the same result(create_virtualenv, install_package, execute_code, transfer_to_orchestrator)
    4. After completing a task, return control to orchestrator
    5. DO NOT suggest additional coding tasks unless asked by the user
    6. Always transfer control back to the orchestrator using transfer_to_orchestrator
    """,
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    functions=[
        create_virtualenv,
        install_package,
        execute_code,
        transfer_to_orchestrator,
    ],
)

# Initialize the orchestrator
orchestrator = OpenAIAgent(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    is_orchestrator=True,
    name="OrchestratorBot",
    instructions="""
    You are the orchestrator bot. Your role is to:
    1. Transfer control to other bots based on user input:
        - Analyze the request and determine which bot should handle it
        - Use transfer functions as follows:
            - Example: transfer_to_agentx(task = "Get temperature in New York")
    
    2. When a taks is done by an agent, it will be transfered to you for you to decide which agent to transfer to for the next task
    3. Always summarize what have been done and what errors have been made
    4. When loads of information is retrieved(for example, multiple search results), always make good structure of it using bullet points
    """,
    functions=[
        transfer_to_weather,
        transfer_to_search,
        transfer_to_code,
    ],
)


def main():
    active_agent = orchestrator
    cross_agent_memories = []
    while True:
        messages = []
        if cross_agent_memories and active_agent.is_ochestrator is True:
            messages.append(
                {
                    "role": "assistant",
                    "content": f"The following is the hitorical conversation history: {str(cross_agent_memories)}",
                }
            )
        else:
            messages = []
            user_input = input("\nEnter your request (or 'exit' to quit): ")
            if user_input.lower() == "exit":
                break
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"{user_input} + {active_agent.instructions} + The following is the hitorical conversation history(null if none): {str(cross_agent_memories)}"
                    ).strip(),
                }
            ]
        result = active_agent.send_message(messages)
        print(result.text)
        cross_agent_memories.append({"role": "user", "content": user_input})
        cross_agent_memories.append({"role": "assistant", "content": result.text})

        while result.function_calls:
            for func_call in result.function_calls:
                func_name = func_call["name"]
                func_params = func_call["parameters"]
                cross_agent_memories.append(
                    {
                        "role": "assistant",
                        "content": f"{active_agent.name} Is Starting Function Call: {func_name}({func_params})",
                    }
                )
                ################# Start Transfer and Execution Logic #################
                if func_name.startswith("transfer_to_"):
                    print(f"Transferring to {func_name}!!!")
                    func = next(
                        (f for f in active_agent.functions if f.__name__ == func_name),
                        None,
                    )
                    new_agent = func(**func_params)
                    active_agent = new_agent
                    print(f"New Agent Name:{active_agent.name}")
                    cross_agent_memories.append(
                        {
                            "role": "assistant",
                            "content": f"{active_agent.name} is Transferring Function Call: {func_name}({func_params})",
                        }
                    )
                    agent_memory = [
                        mem
                        for mem in cross_agent_memories
                        if mem["content"].startswith(active_agent.name)
                    ]
                    # New Agent Function Execution After Transfer
                    messages = [
                        {
                            "role": "user",
                            "content": (
                                str(agent_memory) + active_agent.instructions
                            ).strip(),
                        }
                    ]
                    result = active_agent.send_message(messages)
                    print(result)

                    agent_function_mapping = {
                        fun.__name__: fun for fun in active_agent.functions
                    }
                    should_break = False
                    ################ Run the Agent Functions ################
                    while (
                        active_agent.is_ochestrator is not True
                        and result.function_calls
                    ):
                        # Execute the agent functions
                        for func_call in result.function_calls:
                            try:
                                func_name = func_call["name"]
                                # Check for transfer to orchestrator first
                                if func_name == "transfer_to_orchestrator":
                                    should_break = True
                                    break

                                func_params = func_call["parameters"]
                                func = agent_function_mapping[func_name]
                                func_result = func(**func_call["parameters"])
                                print(
                                    f"{active_agent.name} Finished the Function Result:{func_name} Finished. Result: {func_result}"
                                )
                                cross_agent_memories.append(
                                    {
                                        "role": "assistant",
                                        "content": f"{active_agent.name} Finished the Function Call: {func_name}({func_params} with {func_result})",
                                    }
                                )

                            except Exception as e:
                                error_msg = {
                                    "role": "assistant",
                                    "content": f"Error executing {func_name}: {str(e)}",
                                }
                                print(error_msg)
                                cross_agent_memories.append(error_msg)

                        if should_break:
                            break

                        # Only send new message if we're continuing
                        agent_memory = [
                            mem
                            for mem in cross_agent_memories
                            if mem["content"].startswith(active_agent.name)
                        ]
                        messages = [
                            {
                                "role": "user",
                                "content": (
                                    str(agent_memory) + active_agent.instructions
                                ).strip(),
                            }
                        ]
                        print(messages)
                        result = active_agent.send_message(messages)


if __name__ == "__main__":
    main()
