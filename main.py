"""Main entry point for the agent framework"""

import os
from dotenv import load_dotenv
from smart_team.agents.anthropic_agent import AnthropicAgent
from smart_team.agents.agent_functions import (
    create_virtualenv,
    install_package,
    execute_code,
    get_weather,
)
from smart_team.agents.base_agent import BaseAgent


def main():
    """Main function to run the agent framework"""
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    def transfer_to_code() -> BaseAgent:
        """Transfer control to the Code bot"""
        return code_bot

    def transfer_to_weather() -> BaseAgent:
        """Transfer control to the weather bot"""
        return weather_bot

    def transfer_to_orchestrator() -> BaseAgent:
        """Transfer control back to the orchestrator"""
        return orchestrator

    # Initialize the weather bot
    weather_bot = AnthropicAgent(
        name="WeatherBot",
        instructions="""
        You are the weather bot. Your role is to:
        1. Get weather information for specified locations if not already retrieved
        2. If weather was already checked (in completed_function_calls), just summarize the results
        3. Return to the orchestrator after completing the task
        Note: Always check completed_function_calls before making new requests
        """,
        api_key=api_key,
        functions=[get_weather, transfer_to_orchestrator],
    )

    # Initialize the code bot
    code_bot = AnthropicAgent(
        name="CodeBot",
        instructions="""You are the coding assistant. Your role is to:
        1. Help users with coding tasks and questions
        2. Create env (always use the name python_env), install related packages, generate, analyze and debug code
        3. When installing packages, you MUST:
           - List ALL required packages in a SINGLE response
           - Call install_package function for EACH package in the SAME response
           - Example: If you need packages A, B, and C, return ALL three install_package calls at once
           - Never split package installations across multiple responses
        """,
        api_key=api_key,
        functions=[
            create_virtualenv,
            install_package,
            execute_code,
            transfer_to_orchestrator,
        ],
    )

    # Initialize the orchestrator
    orchestrator = AnthropicAgent(
        name="OrchestratorBot",
        instructions="""
        You are the orchestrator bot. Your role is to:
        1. Understand user requests and determine which bot should handle them
        2. Transfer control to the appropriate bot if the task hasn't been completed
        3. If a task has already been completed (check completed_function_calls), summarize the results instead of transferring
        4. Maintain context and ensure smooth handoffs
        """,
        api_key=api_key,
        functions=[transfer_to_code, transfer_to_weather],
    )

    active_agent = orchestrator
    while True:
        try:
            # Get user input
            user_input = input("User: ")
            if not user_input:
                continue

            # Process user input through active agent
            result = active_agent.send_message(user_input)
            print(f"{active_agent.name} response:", result)

            # Process any function calls
            while result and result.function_calls:
                executed_functions = []
                transfer_functions = []
                regular_functions = []

                # Separate transfer and regular functions
                for function_call in result.function_calls:
                    if function_call["name"].startswith("transfer_to_"):
                        transfer_functions.append(function_call)
                    else:
                        regular_functions.append(function_call)

                # Execute all regular functions in batch
                if regular_functions:
                    for function_call in regular_functions:
                        func_name = function_call["name"]
                        params = function_call["parameters"]

                        func = next(
                            (
                                f
                                for f in active_agent.functions
                                if f.__name__ == func_name
                            ),
                            None,
                        )
                        if func:
                            try:
                                print(
                                    f"Executing function {func_name} with params {params}"
                                )
                                func_result = func(**params)
                                executed_functions.append(
                                    f"Function {func_name} completed with result: {func_result}"
                                )
                                if func_name not in [
                                    call["name"]
                                    for call in active_agent.completed_function_calls
                                ]:
                                    active_agent.add_completed_function(
                                        func_name, params
                                    )
                            except Exception as e:
                                error_msg = (
                                    f"Function {func_name} failed with error: {str(e)}"
                                )
                                print(error_msg)
                                executed_functions.append(error_msg)

                    # Send all function results at once
                    if executed_functions:
                        print("Sending function results to agent:", executed_functions)
                        result = active_agent.send_function_results(executed_functions)
                        print(f"{active_agent.name} response:", result)
                        continue

                # Handle transfer if there are any transfer functions
                if transfer_functions:
                    function_call = transfer_functions[0]  # Process first transfer
                    func_name = function_call["name"]
                    func = next(
                        (f for f in active_agent.functions if f.__name__ == func_name),
                        None,
                    )
                    if func:
                        print(f"Transferring to {func_name.split('_')[-1]}")
                        # Share completed function calls with the next agent
                        next_agent = func()
                        next_agent.completed_function_calls = active_agent.completed_function_calls.copy()
                        next_agent.current_task = active_agent.current_task
                        active_agent = next_agent
                        result = active_agent.send_message(user_input)
                        print(f"{active_agent.name} response:", result)
                        continue

                # If we get here with no executed functions and no transfers, break the loop
                break

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    main()
