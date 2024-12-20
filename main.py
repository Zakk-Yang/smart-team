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
from smart_team.agents.base_agent import BaseAgent, AgentState


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
        1. Get weather information for specified locations
        2. After completing the task, return control to orchestrator
        3. DO NOT suggest additional weather checks unless asked by the user
        """,
        api_key=api_key,
        functions=[get_weather, transfer_to_orchestrator],
    )

    # Initialize the code bot
    code_bot = AnthropicAgent(
        name="CodeBot",
        instructions="""
        You are the coding assistant. Your role is to:
        1. Help users with coding tasks and questions
        2. Create env (stick to the env name as python_env), install packages, generate and debug code
        3. After completing a task, return control to orchestrator
        4. DO NOT suggest additional coding tasks unless asked by the user
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
        1. For NEW user requests:
           - Analyze the request and determine which bot should handle it
           - Transfer control to the appropriate bot using transfer functions
        
        2. For COMPLETED tasks (when control returns to you):
           - DO NOT analyze the request again
           - DO NOT transfer to any other bot
           - Simply print: "What would you like to do next?"
           - Wait for new user input

        3. When you see completed function calls in your history:
           - Consider those tasks as already done
           - DO NOT try to execute them again
           - DO NOT transfer to another bot to repeat them
        """,
        api_key=api_key,
        functions=[transfer_to_code, transfer_to_weather],
    )

    active_agent = orchestrator

    while True:
        try:
            user_input = input("\nEnter your request (or 'exit' to quit): ")
            if user_input.lower() == "exit":
                break

            # Process user input with current agent
            result = active_agent.send_message(user_input)
            if result.text:
                print(f"\n{result.text}")

            # Process any function calls
            while result and result.function_calls:
                executed_functions = []
                current_calls = result.function_calls
                result.function_calls = []  # Reset to avoid infinite loop

                for func_call in current_calls:
                    func_name = func_call["name"]
                    print(f"\nExecuting {func_name}...")

                    if func_name.startswith("transfer_to_"):
                        print(f"Transferring to {func_name.split('_')[-1]}")
                        # Get transfer function
                        transfer_func = next(
                            (f for f in active_agent.functions if f.__name__ == func_name),
                            None
                        )
                        if not transfer_func:
                            print(f"Error: Transfer function {func_name} not found")
                            continue

                        # Share state with the next agent
                        next_agent = transfer_func()
                        next_agent.completed_function_calls = active_agent.completed_function_calls.copy()
                        next_agent.current_task = active_agent.current_task
                        next_agent.messages = active_agent.messages.copy()
                        
                        active_agent = next_agent
                        result = active_agent.send_message(user_input)
                        if result.text:
                            print(f"\n{result.text}")
                        break  # Exit the loop after transfer
                    else:
                        # Find and execute regular function
                        func = next(
                            (f for f in active_agent.functions if f.__name__ == func_name),
                            None
                        )
                        if not func:
                            print(f"Error: Function {func_name} not found")
                            continue

                        try:
                            func_result = func(**func_call["parameters"])
                            result_msg = f"Function {func_name} completed with result: {func_result}"
                            print(result_msg)
                            executed_functions.append(result_msg)
                            active_agent.add_completed_function(func_name, func_call["parameters"])
                        except Exception as e:
                            error_msg = f"Error executing {func_name}: {str(e)}"
                            print(error_msg)
                            executed_functions.append(error_msg)

                # Send function results back to agent if any were executed
                if executed_functions:
                    result = active_agent.send_function_results(executed_functions)
                    if result.text:
                        print(f"\n{result.text}")

                    # Check if task is completed and we need to return to orchestrator
                    if active_agent.is_completed() and active_agent != orchestrator:
                        print("\nReturning to orchestrator...")
                        # Copy state back to orchestrator
                        orchestrator.completed_function_calls = active_agent.completed_function_calls.copy()
                        orchestrator.messages = active_agent.messages.copy()
                        orchestrator.reset()  # Reset state to ready
                        active_agent = orchestrator
                        break  # Exit function processing loop

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue


if __name__ == "__main__":
    main()
